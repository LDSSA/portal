from constance import config
from django.conf import settings
from django.utils import timezone


def admissions_open():
    if not settings.ADMISSIONS_ENABLED:
        return False
    return config.ADMISSIONS_APPLICATIONS_OPENING_DATE < timezone.now() <= config.ADMISSIONS_APPLICATIONS_CLOSING_DATE


def admissions_ended():
    if not settings.ADMISSIONS_ENABLED:
        return True
    return timezone.now() > config.ADMISSIONS_APPLICATIONS_CLOSING_DATE
