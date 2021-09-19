import logging
import random
from itertools import zip_longest
from io import StringIO

from django.contrib.contenttypes.models import ContentType

from portal.hackathons.models import Hackathon
from portal.hackathons.models import Attendance
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

    logger.info(f"Student {user.name} has been in {num_presences} out of {num_hackathons} "
                f"hackathons and has {'completed' if present_in_first else 'missed'} the"
                f"first hackathon")

    if not present_in_first or num_presences < num_hackathons - 1:
        logger.info(f"Student {user.name} can not graduate")
        return False

    logger.info(f"Student {user.name} can graduate")
    return True
