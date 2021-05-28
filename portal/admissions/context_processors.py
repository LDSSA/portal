from django.conf import settings
from constance import config


def admissions_context_processor(request):
    my_dict = {
        "PORTAL_STATUS": config.PORTAL_STATUS,
        "ACADEMY_START": config.ACADEMY_START,
        "ADMISSIONS_CODING_TEST_DURATION": config.ADMISSIONS_CODING_TEST_DURATION,
        "ADMISSIONS_APPLICATIONS_START": config.ADMISSIONS_APPLICATIONS_START,
        "ADMISSIONS_SELECTION_START": config.ADMISSIONS_SELECTION_START,
        "ADMISSIONS_ACCEPTING_PAYMENT_PROFS": config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS,
    }

    return my_dict
