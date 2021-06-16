from constance import config

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
        "ACADEMY_START": config.ACADEMY_START,
        "ADMISSIONS_CODING_TEST_DURATION": config.ADMISSIONS_CODING_TEST_DURATION,
        "ADMISSIONS_APPLICATIONS_START": config.ADMISSIONS_APPLICATIONS_START,
        "ADMISSIONS_SELECTION_START": config.ADMISSIONS_SELECTION_START,
        "ADMISSIONS_ACCEPTING_PAYMENT_PROFS": config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS,
        "code_of_conduct_accepted": request.user.code_of_conduct_accepted,
        "scholarship_decided": request.user.applying_for_scholarship is not None,
        "applying_for_scholarship": request.user.applying_for_scholarship is not None,
        "user_has_payment": user_has_payment(request.user),
    }

    return my_dict
