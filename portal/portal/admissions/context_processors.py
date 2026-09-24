from datetime import timedelta
from zoneinfo import ZoneInfo

from constance import config
from django.conf import settings

from portal.admissions.policy import academy_open, registration_changes_open
from portal.selection.models import Selection
from portal.users.models import User


def user_has_payment(user: User) -> bool:
    try:
        return user.selection.payment_value is not None
    except Selection.DoesNotExist:
        return False


def admissions_context_processor(request):
    my_dict = {
        "PORTAL_STATUS": config.PORTAL_STATUS,
        "STUDENT_REPO_NAME": settings.STUDENT_REPO_NAME,
        "no_exam_scheduled": config.NO_EXAM_USE_SCHEDULE,
        "no_exam_payments_start": config.NO_EXAM_PAYMENTS_START.astimezone(
            ZoneInfo("Europe/Lisbon")
        ),
        "no_exam_payments_deadline": (
            config.NO_EXAM_PAYMENTS_END - timedelta(microseconds=1)
        ).astimezone(ZoneInfo("Europe/Lisbon")),
        "ADMISSIONS_PAYMENT_DAYS": config.ADMISSIONS_PAYMENT_DAYS,
        "ACADEMY_START": config.ACADEMY_START,
        "ADMISSIONS_CODING_TEST_DURATION": config.ADMISSIONS_CODING_TEST_DURATION,
        "ADMISSIONS_APPLICATIONS_START": config.ADMISSIONS_APPLICATIONS_START,
        "ADMISSIONS_SELECTION_START": config.ADMISSIONS_SELECTION_START,
        "ADMISSIONS_ACCEPTING_PAYMENT_PROFS": config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS,
        "ADMISSIONS_CODING_TEST_DURATION_HOURS": str(
            config.ADMISSIONS_CODING_TEST_DURATION.total_seconds() / 3600,
        ),
        "ADMISSIONS_APPLICATIONS_STARTED_STATUSES": settings.ADMISSIONS_APPLICATIONS_STARTED_STATUSES,
    }
    if request.user.is_authenticated:
        if request.user.is_student:
            from portal.academy.services import progression_block_reason

            my_dict["course_progression_block_reason"] = progression_block_reason(
                request.user
            )
        my_dict.update(
            {
                "admissions_requires_exam": request.user.admissions_requires_exam,
                "academy_access_open": academy_open(request.user),
                "registration_open": registration_changes_open(request.user),
                "code_of_conduct_accepted": request.user.code_of_conduct_accepted,
                "scholarship_decided": request.user.applying_for_scholarship
                is not None,
                "applying_for_scholarship": request.user.applying_for_scholarship,
                "user_has_payment": user_has_payment(request.user),
            },
        )

    return my_dict
