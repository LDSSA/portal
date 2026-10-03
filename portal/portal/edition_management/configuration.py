"""Reset keeps existing schedules and mode. It never guesses the next calendar."""

from constance import config

CLOSED_SWITCHES = (
    "ACCOUNT_ALLOW_REGISTRATION",
    "NO_EXAM_REGISTRATION_OPEN",
    "NO_EXAM_ACADEMY_ACCESS_OPEN",
    "ADMISSIONS_ACCEPTING_PAYMENT_PROFS",
)


def close_public_access():
    for key in CLOSED_SWITCHES:
        setattr(config, key, False)


def readiness_issues():
    from django.utils import timezone

    from portal.academy.models import Unit
    from portal.admissions.policy import no_exam_schedule_valid

    issues = []
    if not Unit.objects.exists():
        issues.append("No course units are configured.")
    if config.ADMISSIONS_MODE == "no_exam":
        if config.NO_EXAM_USE_SCHEDULE and not no_exam_schedule_valid():
            issues.append("The no-exam calendar is invalid.")
    elif config.ADMISSIONS_APPLICATIONS_START >= config.ADMISSIONS_SELECTION_START:
        issues.append("The exam calendar is invalid.")
    if (
        config.ADMISSIONS_MODE == "no_exam"
        and config.NO_EXAM_USE_SCHEDULE
        and config.NO_EXAM_SIGNUPS_END <= timezone.now()
    ):
        issues.append("Update the no-exam signup dates before opening a new edition.")
    if (
        config.ADMISSIONS_MODE == "exam"
        and config.ADMISSIONS_SELECTION_START <= timezone.now()
    ):
        issues.append("Update the exam admission dates before opening a new edition.")
    return issues
