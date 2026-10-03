"""Enrollment transitions. Lock the user before their selection in every writer."""
from datetime import timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from constance import config
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from portal.admissions.policy import (
    email_verified,
    registration_changes_open,
    registration_ready,
)
from portal.applications.models import Application
from portal.hackathons.models import Attendance, Hackathon
from portal.users.models import (
    AcademyTypePreference,
    TicketType,
    TicketTypeSelectable,
    User,
)

from .domain import SelectionDomain
from .models import EnrollmentEmail, ScholarshipStatus, Selection
from .payment import add_document, add_note, can_be_updated, load_payment_data
from .status import SelectionStatus as S


def _user(user):
    return User.objects.select_for_update().get(pk=user.pk)


def _selection(user):
    try:
        return (
            Selection.objects.select_for_update().select_related("user").get(user=user)
        )
    except Selection.DoesNotExist as exc:
        raise ValidationError("Complete registration first.") from exc


def _staff(actor):
    if not actor.is_active or not (actor.is_staff or actor.is_superuser):
        raise PermissionDenied


def _notify(selection, event, subject, body):
    EnrollmentEmail.objects.get_or_create(
        event_key=f"{selection.pk}:{event}",
        defaults={
            "selection": selection,
            "recipient": selection.user.email,
            "subject": subject,
            "body": body,
        },
    )


def _payment_message(selection):
    due = selection.payment_due_date
    if not selection.user.admissions_requires_exam and config.NO_EXAM_USE_SCHEDULE:
        due -= timedelta(microseconds=1)
    due = due.astimezone(ZoneInfo("Europe/Lisbon"))
    payment_start = (
        "Payment opens on "
        + config.NO_EXAM_PAYMENTS_START.astimezone(ZoneInfo("Europe/Lisbon")).strftime(
            "%Y-%m-%d"
        )
        + ". "
        if not selection.user.admissions_requires_exam and config.NO_EXAM_USE_SCHEDULE
        else ""
    )
    return (
        payment_start + f"Please pay €{selection.payment_value:g} by "
        f"{due:%Y-%m-%d %H:%M} (Lisbon time). "
        f"Log in to {settings.BASE_URL} for bank details, upload payment proof"
        + (
            " and your student ID"
            if selection.ticket_type == TicketType.student
            else ""
        )
        + ", then submit your documents for verification."
    )


def _activate_student(user):
    user.is_student = True
    user.save(update_fields=["is_student", "updated_at"])
    for hackathon in Hackathon.objects.all():
        Attendance.objects.get_or_create(user=user, hackathon=hackathon)


@transaction.atomic
def complete_registration(user, *, allow_closed=False):
    user = _user(user)
    existing = Selection.objects.filter(user=user).first()
    if existing is not None or user.is_student:
        return existing
    if not registration_ready(user):
        return None
    if not allow_closed and not registration_changes_open(user):
        return None
    if user.registration_completed_at is None:
        user.registration_completed_at = timezone.now()
        user.save(update_fields=["registration_completed_at", "updated_at"])
    if user.admissions_requires_exam:
        Application.objects.get_or_create(user=user)
        return None
    if user.applying_for_scholarship:
        user.ticket_type = TicketType.scholarship
        user.save(update_fields=["ticket_type", "updated_at"])
        selection = Selection.objects.create(
            user=user, status=S.INTERVIEW, scholarship_status=ScholarshipStatus.PENDING
        )
        _notify(
            selection,
            "scholarship-pending",
            "Scholarship application received",
            "Your registration is complete. Staff will review your scholarship request. "
            "There is no admission exam. If the scholarship is refused, your admission ends.",
        )
    else:
        if user.ticket_type not in TicketTypeSelectable.values:
            raise ValidationError(
                "Choose a student, regular or company ticket in your profile."
            )
        selection = Selection.objects.create(user=user, status=S.SELECTED)
        load_payment_data(selection)
        _notify(
            selection,
            "payment-requested",
            "Complete your enrollment",
            _payment_message(selection),
        )
    add_note(selection, "No-exam registration completed automatically.", user)
    return selection


@transaction.atomic
def record_registration_step(user, step, value):
    user = _user(user)
    if not user.is_active or user.is_staff or user.is_superuser or user.is_instructor:
        raise PermissionDenied
    if not email_verified(user):
        raise ValidationError("Confirm your email before completing registration.")
    fields = {
        "coc": "code_of_conduct_accepted",
        "scholarship": "applying_for_scholarship",
        "academy_type": "academy_type_preference",
    }
    if step == "academy_type" and not config.ADMISSIONS_ASK_ATTENDANCE_PREFERENCE:
        raise ValidationError("The attendance preference survey is disabled.")
    if step not in fields:
        raise ValidationError("Unknown registration step.")
    if step == "coc" and value is not True:
        raise ValidationError("Accept the code of conduct and refund policy.")
    if step == "scholarship" and type(value) is not bool:
        raise ValidationError("Choose yes or no.")
    if step != "coc" and not user.code_of_conduct_accepted:
        raise ValidationError("Accept the code of conduct first.")
    if step == "academy_type" and (
        user.applying_for_scholarship is None
        or value not in AcademyTypePreference.values
    ):
        raise ValidationError(
            "Decide about a scholarship, then choose a valid attendance preference."
        )
    field = fields[step]
    old = getattr(user, field)
    if Selection.objects.filter(user=user).exists() or user.is_student:
        if old == value:
            return
        raise ValidationError(
            "Registration is complete. Contact admissions to request a correction."
        )
    if not registration_changes_open(user):
        raise ValidationError("Registration is closed.")
    if step == "scholarship" and old is not None and old != value:
        raise ValidationError("Your scholarship decision cannot be changed.")
    setattr(user, field, value)
    if step == "scholarship" and value:
        user.ticket_type = TicketType.scholarship
    user.save(update_fields=[field, "ticket_type", "updated_at"])
    return complete_registration(user)


@transaction.atomic
def review_scholarship(user, actor, action, message=""):
    _staff(actor)
    user = _user(user)
    selection = _selection(user)
    if action == "note":
        if not message.strip():
            raise ValidationError("Write a note.")
        add_note(selection, message, actor)
        return
    if action not in ("accept", "reject") or selection.status != S.INTERVIEW:
        raise ValidationError("This scholarship is not awaiting a decision.")
    if action == "reject" and not message.strip():
        raise ValidationError("Explain the scholarship refusal.")
    selection.scholarship_status = (
        ScholarshipStatus.APPROVED if action == "accept" else ScholarshipStatus.REJECTED
    )
    selection.scholarship_decided_at = timezone.now()
    selection.scholarship_decided_by = actor
    selection.save()
    if action == "accept":
        user.ticket_type = TicketType.scholarship
        user.save(update_fields=["ticket_type", "updated_at"])
        selection.user = user
        load_payment_data(selection)
        SelectionDomain.manual_update_status(selection, S.SELECTED, actor, msg=message)
        _notify(
            selection,
            "scholarship-approved",
            "Scholarship approved",
            _payment_message(selection),
        )
    else:
        SelectionDomain.manual_update_status(selection, S.REJECTED, actor, msg=message)
        _notify(
            selection,
            "scholarship-rejected",
            "Scholarship decision",
            f"Your scholarship request was refused and your admission has ended. {message}",
        )


def _require_documents(selection):
    if not selection.documents.filter(doc_type="payment_proof").exists():
        raise ValidationError("Upload payment proof first.")
    if (
        selection.ticket_type == TicketType.student
        and not selection.documents.filter(doc_type="student_id").exists()
    ):
        raise ValidationError("Upload your student ID first.")


@transaction.atomic
def upload_document(user, document, document_type):
    user = _user(user)
    selection = _selection(user)
    if not email_verified(user) or not can_be_updated(selection):
        raise ValidationError("Document uploads are closed for this application.")
    if document_type not in ("payment_proof", "student_id") or not document:
        raise ValidationError("Choose a document to upload.")
    add_document(selection, document, document_type)


@transaction.atomic
def submit_payment(user):
    user = _user(user)
    selection = _selection(user)
    if not email_verified(user) or not can_be_updated(selection):
        raise ValidationError("Payment documents cannot be submitted now.")
    _require_documents(selection)
    if selection.status != S.TO_BE_ACCEPTED:
        SelectionDomain.manual_update_status(selection, S.TO_BE_ACCEPTED, user)


@transaction.atomic
def review_payment(user, actor, action, message=""):
    _staff(actor)
    user = _user(user)
    selection = _selection(user)
    if action == "note":
        if not message.strip():
            raise ValidationError("Write a note.")
        add_note(selection, message, actor)
        return
    if action == "accept" and selection.status == S.ACCEPTED:
        return
    if selection.status != S.TO_BE_ACCEPTED or action not in (
        "accept",
        "reject",
        "ask_additional",
    ):
        raise ValidationError("Payment is not awaiting review.")
    if action != "accept" and not message.strip():
        raise ValidationError("Explain your decision to the applicant.")
    if action == "accept":
        if not registration_ready(user):
            raise ValidationError(
                "The applicant must verify their email and complete registration."
            )
        if selection.payment_value is None:
            raise ValidationError("Payment details have not been issued.")
        if (
            not user.admissions_requires_exam
            and user.applying_for_scholarship
            and selection.scholarship_status != ScholarshipStatus.APPROVED
        ):
            raise ValidationError("Approve the scholarship before accepting payment.")
        _require_documents(selection)
        SelectionDomain.manual_update_status(selection, S.ACCEPTED, actor, msg=message)
        if not user.admissions_requires_exam:
            _activate_student(user)
        _notify(
            selection,
            "payment-accepted",
            "Payment verified",
            "Your payment was verified. "
            + (
                "Staff will finalize admissions before student access opens. "
                if user.admissions_requires_exam
                else "Your enrollment is complete. Course access opens on the academy start date once staff enable it. "
            )
            + message,
        )
    elif action == "ask_additional":
        SelectionDomain.manual_update_status(selection, S.SELECTED, actor, msg=message)
        _notify(
            selection,
            f"payment-additional-{uuid4().hex}",
            "Additional payment documents needed",
            message,
        )
    else:
        SelectionDomain.manual_update_status(selection, S.REJECTED, actor, msg=message)
        _notify(
            selection,
            "payment-rejected",
            "Payment refused",
            f"Your admission has ended. {message}",
        )


@transaction.atomic
def reset_payment(user, actor, reason, ticket_type=None):
    _staff(actor)
    user = _user(user)
    selection = _selection(user)
    if selection.status != S.SELECTED or not reason.strip():
        raise ValidationError(
            "Reset requires a reason and an application awaiting payment documents."
        )
    if ticket_type:
        if (
            user.applying_for_scholarship
            or ticket_type not in TicketTypeSelectable.values
        ):
            raise ValidationError("Only non-scholarship tickets can be changed.")
        user.ticket_type = ticket_type
        user.save(update_fields=["ticket_type", "updated_at"])
        selection.user = user
    load_payment_data(selection, actor, reset=True)
    add_note(selection, reason, actor)
    _notify(
        selection,
        f"payment-reset-{uuid4().hex}",
        "Updated payment instructions",
        _payment_message(selection),
    )
