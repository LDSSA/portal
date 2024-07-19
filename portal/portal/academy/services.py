import csv  # noqa: D100
import logging
from io import StringIO

from django.db.models import Max

from portal.academy.models import Grade, Specialization, Unit
from portal.hackathons.models import Attendance, Hackathon
from portal.users.models import User

logger = logging.getLogger(__name__)

PASSING_SCORE = 16


def csvdata(spc_list, unit_list, object_list):  # noqa: ANN001, ANN201, D103
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
        user_row = user + [grade.score or grade.status for grade in obj["grades"] if grade]
        rows.append(user_row)

    for row in rows:
        csvwriter.writerow(row)

    return csvfile.getvalue()


def check_graduation_status(user: User):  # noqa: ANN201
    """Check graduation eligibility of student given their attendance in hackathons.

    - if student missed the first hackathon, they can not not graduate
    - if student has missed more than one hackathon, they can not not graduate
    - otherwise the student can still graduate

    """
    logger.info("Checking graduation status for %s", user.name)

    if user.failed_or_dropped:
        return False

    attendances = Attendance.objects.filter(user=user)
    first_hackathon = Hackathon.objects.order_by("due_date").first()
    num_hackathons = Hackathon.objects.count()

    # TODO: set hackathon 1 as mandatory and verify for mandatory hackathons  # noqa: FIX002, TD002, TD003
    num_presences = attendances.filter(present=True).count()
    present_in_first = attendances.filter(hackathon=first_hackathon).first().present

    logger.info(
        f"Student {user.username} has been in {num_presences} out of {num_hackathons} "  # noqa: G004
        f"hackathons and has {'completed' if present_in_first else 'missed'} the"
        f"first hackathon",
    )

    if not present_in_first or num_presences < num_hackathons - 1:
        logger.info("Student %s can not graduate", user.username)
        return False

    logger.info("Student %s can graduate", user.username)
    return True


def check_complete_specialization(user: User, spec: Specialization):  # noqa: ANN201
    """Check student completed a specialization.

    Verifies if the student passed on all units
    """
    logger.info("Checking %s completion of specialization: %s", user.name, spec.name)

    spec_units = list(Unit.objects.filter(specialization=spec))
    spec_units_codes = [u.code for u in spec_units]

    # TODO: when grades contain info about submission before/after deadline  # noqa: FIX002, TD002, TD003
    #  filter only by grades submitted within deadline
    passed_unit_codes = []
    for unit in spec_units:
        top_score = (
            Grade.objects.filter(user=user, unit=unit).aggregate(Max("score"))["score__max"] or 0
        )

        if top_score >= PASSING_SCORE:
            passed_unit_codes.append(unit.code)

    logger.info("Student %s has passed units %s in %s", user.username, passed_unit_codes, spec.name)

    if sorted(passed_unit_codes) == sorted(spec_units_codes):
        logger.info("Student %s completed specialization %s", user.username, spec.name)
        return True

    logger.info("Student %s did not complete specialization %s", user.username, spec.name)
    return False


def get_last_grade(unit, user):  # noqa: ANN001, ANN201, D103
    grade = unit.grades.filter(user=user).order_by("-created").first()
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade


def get_best_grade(unit, user):  # noqa: ANN001, ANN201, D103
    grade = unit.grades.filter(user=user, status="graded", on_time=True).order_by("-score").first()
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade
