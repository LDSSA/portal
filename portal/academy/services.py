import logging
import random
from itertools import zip_longest
from io import StringIO

from django.contrib.contenttypes.models import ContentType

from portal.academy.models import Specialization, Grade, Unit
from portal.hackathons.models import Hackathon, Attendance
from portal.users.models import User


logger = logging.getLogger(__name__)


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
    present_in_first = attendances.filter(hackathon=first_hackathon).first().present

    logger.info(f"Student {user.username} has been in {num_presences} out of {num_hackathons} "
                f"hackathons and has {'completed' if present_in_first else 'missed'} the"
                f"first hackathon")

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
    logger.info(f"Checking {user.name} completion of specialization: {spec.name}")

    spec_units = [unit for unit in Unit.objects.filter(specialization=spec)]
    spec_units_codes = [u.code for u in spec_units]

    # TODO: when grades contain info about submission before/after deadline
    #  filter only by grades submitted within deadline
    passed_unit_codes = []
    for unit in spec_units:
        unit_grades = Grade.objects.filter(user=user, unit=unit)
        scores = [g.score for g in unit_grades]
        top_score = max(scores) if scores else 0.0

        if top_score >= 16:
            passed_unit_codes.append(unit.code)

    logger.info(f"Student {user.username} has passed units {passed_unit_codes} in {spec.name}")

    if sorted(passed_unit_codes) == sorted(spec_units_codes):
        logger.info(f"Student {user.username} completed specialization {spec.name}")
        return True

    logger.info(f"Student {user.username} did not complete specialization {spec.name}")
    return False
