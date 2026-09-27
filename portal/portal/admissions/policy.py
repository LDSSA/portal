"""Separate an applicant's workflow from the legacy exam calendar."""
from allauth.account.models import EmailAddress
from constance import config
from django.utils import timezone

from portal.users.models import (
    AcademyTypePreference,
    AdmissionsMode,
    Gender,
    TicketType,
)


def email_verified(user):
    return EmailAddress.objects.filter(
        user=user, email__iexact=user.email, verified=True
    ).exists()


def attendance_preference_satisfied(user):
    """Waive only the survey requirement for already-completed registrations."""
    if (
        not config.ADMISSIONS_ASK_ATTENDANCE_PREFERENCE
        or user.academy_type_preference in AcademyTypePreference.values
        or user.registration_completed_at is not None
        or user.is_student
    ):
        return True
    # Legacy exam selections may predate registration_completed_at.
    from portal.selection.models import Selection

    return Selection.objects.filter(user=user).exists()


def registration_ready(user):
    return bool(
        user.is_active
        and not (user.is_staff or user.is_superuser or user.is_instructor)
        and user.name.strip()
        and user.gender in Gender.values
        and user.ticket_type in TicketType.values
        and email_verified(user)
        and user.code_of_conduct_accepted
        and user.applying_for_scholarship is not None
        and attendance_preference_satisfied(user)
    )


def registration_changes_open(user):
    if user.admissions_requires_exam:
        return config.PORTAL_STATUS.startswith("admissions")
    return config.NO_EXAM_REGISTRATION_OPEN and (
        not config.NO_EXAM_USE_SCHEDULE
        or (
            no_exam_schedule_valid()
            and config.NO_EXAM_SIGNUPS_START
            <= timezone.now()
            < config.NO_EXAM_REGISTRATION_END
        )
    )


def academy_open(user):
    if user.admissions_requires_exam:
        return config.PORTAL_STATUS == "academy"
    return config.NO_EXAM_ACADEMY_ACCESS_OPEN and timezone.now() >= config.ACADEMY_START


def new_signups_open():
    if not config.ACCOUNT_ALLOW_REGISTRATION:
        return False
    if config.ADMISSIONS_MODE == AdmissionsMode.NO_EXAM:
        return config.NO_EXAM_REGISTRATION_OPEN and (
            not config.NO_EXAM_USE_SCHEDULE
            or (
                no_exam_schedule_valid()
                and config.NO_EXAM_SIGNUPS_START
                <= timezone.now()
                < config.NO_EXAM_SIGNUPS_END
            )
        )
    return (
        config.ADMISSIONS_MODE == AdmissionsMode.EXAM
        and config.ADMISSIONS_APPLICATIONS_START < config.ADMISSIONS_SELECTION_START
        and timezone.now() < config.ADMISSIONS_SELECTION_START
    )


def payment_window_open(user):
    if user.admissions_requires_exam or not config.NO_EXAM_USE_SCHEDULE:
        return True
    return (
        no_exam_schedule_valid()
        and config.NO_EXAM_PAYMENTS_START
        <= timezone.now()
        < config.NO_EXAM_PAYMENTS_END
    )


def no_exam_schedule_valid():
    return (
        config.NO_EXAM_SIGNUPS_START
        < config.NO_EXAM_SIGNUPS_END
        <= config.NO_EXAM_REGISTRATION_END
        <= config.NO_EXAM_PAYMENTS_END
        and config.NO_EXAM_PAYMENTS_START < config.NO_EXAM_PAYMENTS_END
    )
