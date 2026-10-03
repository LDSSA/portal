import csv
import logging
from datetime import datetime, time, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from portal.academy.models import Grade, GradeDeadlineDecision, Specialization, Unit
from portal.hackathons.models import Attendance, Hackathon
from portal.users.models import User

logger = logging.getLogger(__name__)

PASSING_SCORE = 16


def csvdata(spc_list, unit_list, object_list):
    csvfile = StringIO()
    csvwriter = csv.writer(csvfile)

    headers = ["username", "slack_id", "submission_date", "total_score"]
    specs = []
    for spc in spc_list:
        specs.extend([spc.code for _ in range(spc.unit_count)])

    first_row = headers + [
        spc + "-" + unit.code for spc, unit in zip(specs, unit_list, strict=True)
    ]

    rows = [first_row]
    for obj in object_list:
        user = [
            obj["user"].username,
            obj["user"].slack_member_id,
            obj["submission_date"],
            obj["total_score"],
        ]
        user_row = user + [
            (grade.score if grade.score is not None else grade.status) if grade else ""
            for grade in obj["grades"]
        ]
        rows.append(user_row)

    for row in rows:
        csvwriter.writerow(row)

    return csvfile.getvalue()


def unit_deadline(unit):
    """Exclusive end of the due date in Lisbon, including DST transitions."""
    return datetime.combine(
        unit.due_date + timedelta(days=1), time.min, tzinfo=ZoneInfo("Europe/Lisbon")
    )


def valid_deadline_filter():
    return Q(deadline_valid_override=True) | Q(
        deadline_valid_override__isnull=True, on_time=True
    )


def qualifying_grades(user):
    return Grade.objects.filter(
        valid_deadline_filter(), user=user, status="graded", score__gte=PASSING_SCORE
    )


def check_complete_specialization(user: User, spec: Specialization):
    required = Unit.objects.filter(specialization=spec, required_for_certificate=True)
    passed = qualifying_grades(user).values_list("unit_id", flat=True)
    return required.exists() and not required.exclude(pk__in=passed).exists()


def check_graduation_status(user: User):
    """Provisional certificate eligibility; never an access restriction.

    Future work/attendance is not a failure. In-flight timely grading remains
    pending until its result is known. Completion of capstone is assessed separately.
    """
    if user.failed_or_dropped:
        return False
    passed = set(qualifying_grades(user).values_list("unit_id", flat=True))
    pending = set(
        Grade.objects.filter(
            valid_deadline_filter(), user=user, status__in=("sent", "grading")
        ).values_list("unit_id", flat=True)
    )
    for unit in Unit.objects.filter(required_for_certificate=True):
        if timezone.now() >= unit_deadline(unit) and unit.pk not in passed | pending:
            return False
    completed = Hackathon.objects.filter(status="complete")
    present = set(
        Attendance.objects.filter(user=user, present=True).values_list(
            "hackathon_id", flat=True
        )
    )
    missed = [h for h in completed if h.pk not in present]
    # Preserve the existing allowance of one missed non-mandatory hackathon.
    return len(missed) <= 1 and not any(
        h.code.upper() in ("HCKT01", "HCKT06") for h in missed
    )


def refresh_certificate_eligibility(user):
    eligible = check_graduation_status(user)
    if user.can_graduate != eligible:
        User.objects.filter(pk=user.pk).update(can_graduate=eligible)
        user.can_graduate = eligible
    return eligible


def get_last_grade(unit, user):
    grade = unit.grades.filter(user=user).order_by("-created").first()
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade


def get_best_grade(unit, user):
    grade = (
        unit.grades.filter(valid_deadline_filter(), user=user, status="graded")
        .order_by("-score")
        .first()
    )
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade


def progression_block_reason(user):
    """No-exam S01/H1 progression gate, independent of later certification."""
    if user.admissions_requires_exam:
        return ""
    spec = Specialization.objects.filter(code="S01").first()
    if spec is None:
        return "S01 has not been configured yet. Contact the instructors."
    if not check_complete_specialization(user, spec):
        return (
            "You must pass every mandatory S01 unit with at least 16/20 by its deadline "
            "before entering Hackathon 1 or later course activities. You can still view "
            "S01 and contact staff about pending grades or submission problems."
        )
    h1 = Hackathon.objects.filter(code="HCKT01", status="complete").first()
    if (
        h1
        and not Attendance.objects.filter(
            user=user, hackathon=h1, present=True
        ).exists()
    ):
        return "Hackathon 1 attendance is mandatory to continue the course. Contact staff if your attendance record is incorrect."
    return ""


@transaction.atomic
def set_deadline_override(grade_id, actor, value, reason):
    """Audit a superuser deadline decision without rewriting submission evidence."""
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied("Only a superuser may override deadline validity.")
    if value is not None and type(value) is not bool:
        raise ValidationError("Choose automatic, valid or invalid.")
    if not reason or not reason.strip():
        raise ValidationError("A justification is required for every override change.")
    user_id = Grade.objects.values_list("user_id", flat=True).get(pk=grade_id)
    user = User.objects.select_for_update().get(pk=user_id)
    grade = Grade.objects.select_for_update().get(pk=grade_id)
    reason = reason.strip()
    if (
        grade.deadline_valid_override == value
        and grade.deadline_override_reason == reason
    ):
        return grade
    GradeDeadlineDecision.objects.create(
        grade=grade,
        previous_value=grade.deadline_valid_override,
        new_value=value,
        reason=reason,
        actor=actor,
        actor_username=actor.username,
    )
    Grade.objects.filter(pk=grade_id).update(
        deadline_valid_override=value,
        deadline_override_reason=reason,
        deadline_override_by=actor,
        deadline_override_at=timezone.now(),
    )
    grade.refresh_from_db()
    refresh_certificate_eligibility(user)
    return grade
