from constance import config  # noqa: D100
from django.conf import settings

from portal.selection.models import Selection
from portal.users.models import User


def user_has_payment(user: User) -> bool:  # noqa: D103
    try:
        return user.selection.payment_value is not None
    except Selection.DoesNotExist:
        return False


def admissions_context_processor(request):  # noqa: ANN001, ANN201, D103
    my_dict = {
        "PORTAL_STATUS": config.PORTAL_STATUS,
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
        my_dict.update(
            {
                "code_of_conduct_accepted": request.user.code_of_conduct_accepted,
                "scholarship_decided": request.user.applying_for_scholarship is not None,
                "applying_for_scholarship": request.user.applying_for_scholarship,
                "user_has_payment": user_has_payment(request.user),
            },
        )

    return my_dict
