import csv
import logging
from io import StringIO

from django.db.models import Max
from portal.academy.models import Specialization, Grade, Unit
from portal.hackathons.models import Hackathon, Attendance
from portal.users.models import User


logger = logging.getLogger(__name__)


def csvdata(spc_list, unit_list, object_list):
    csvfile = StringIO()
    csvwriter = csv.writer(csvfile)

    headers = ["username", "slack_id", "submission_date", "total_score"]
    specs = []
    for spc in spc_list:
        specs.extend([spc.code for _ in range(spc.unit_count)])

    first_row = headers + [spc + "-" + unit.code for spc, unit in zip(specs, unit_list)]

    rows = [first_row]
    for obj in object_list:
        user = [
            obj["user"].username,
            obj["user"].slack_member_id,
            obj["submission_date"],
            obj["total_score"],
        ]
        user_row = user + [
            grade.score or grade.status for grade in obj["grades"] if grade
        ]
        rows.append(user_row)

    for row in rows:
        csvwriter.writerow(row)

    return csvfile.getvalue()


def check_graduation_status(user: User):
    """
    Check graduation eligibility of student given their attendance in hackathons:

    - if student missed the first hackathon, they can not not graduate
    - if student has missed more than one hackathon, they can not not graduate
    - otherwise the student can still graduate

    """
    logger.info(f"Checking graduation status for {user.name}")

    attendances = Attendance.objects.filter(user=user)
    first_hackathon = Hackathon.objects.order_by("due_date").first()
    num_hackathons = Hackathon.objects.count()

    # TODO: set hackathon 1 as mandatory and verify for mandatory hackathons
    num_presences = attendances.filter(present=True).count()
    present_in_first = (
        attendances.filter(hackathon=first_hackathon).first().present
    )

    logger.info(
        f"Student {user.username} has been in {num_presences} out of {num_hackathons} "
        f"hackathons and has {'completed' if present_in_first else 'missed'} the"
        f"first hackathon"
    )

    if not present_in_first or num_presences < num_hackathons - 1:
        logger.info(f"Student {user.username} can not graduate")
        return False

    logger.info(f"Student {user.username} can graduate")
    return True


def check_complete_specialization(user: User, spec: Specialization):
    """
    Check student completed a specialization by verifying
    they passed on all units
    """
    logger.info(
        f"Checking {user.name} completion of specialization: {spec.name}"
    )

    spec_units = [unit for unit in Unit.objects.filter(specialization=spec)]
    spec_units_codes = [u.code for u in spec_units]

    # TODO: when grades contain info about submission before/after deadline
    #  filter only by grades submitted within deadline
    passed_unit_codes = []
    for unit in spec_units:
        top_score = (
            Grade.objects.filter(user=user, unit=unit).aggregate(Max("score"))[
                "score__max"
            ]
            or 0
        )

        if top_score >= 16:
            passed_unit_codes.append(unit.code)

    logger.info(
        f"Student {user.username} has passed units {passed_unit_codes} in {spec.name}"
    )

    if sorted(passed_unit_codes) == sorted(spec_units_codes):
        logger.info(
            f"Student {user.username} completed specialization {spec.name}"
        )
        return True

    logger.info(
        f"Student {user.username} did not complete specialization {spec.name}"
    )
    return False


def get_last_grade(unit, user):
    grade = unit.grades.filter(user=user).order_by("-created").first()
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade


def get_best_grade(unit, user):
    grade = (
        unit.grades.filter(user=user, on_time=True).order_by("-score").first()
    )
    if grade is None:
        grade = Grade(user=user, unit=unit)
    return grade
