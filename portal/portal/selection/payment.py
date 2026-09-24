from datetime import datetime, timedelta, timezone
from logging import getLogger

from constance import config
from django.core.exceptions import ValidationError

from portal.admissions.policy import payment_window_open

from .logs import SelectionEvent, log_selection_event
from .models import Selection, SelectionDocument
from .status import SelectionStatus

logger = getLogger(__name__)


PRICE_TABLE = {
    "student": 250,
    "regular": 500,
    "company": 1500,
    "scholarship": 20,
}


class PaymentExceptionError(Exception):
    pass


def load_payment_data(selection, staff=None, *, reset=False):
    if selection.payment_value is not None and not reset:
        return
    if config.ADMISSIONS_PAYMENT_DAYS < 1:
        raise ValidationError("Payment days must be positive.")
    if selection.user.ticket_type not in PRICE_TABLE:
        raise ValidationError("Choose a valid ticket type before issuing payment.")
    old_ticket_type = selection.ticket_type
    old_value = selection.payment_value

    ticket_type = selection.user.ticket_type
    value = PRICE_TABLE[ticket_type]

    selection.ticket_type = ticket_type
    selection.payment_value = value
    selection.payment_due_date = datetime.now(timezone.utc) + timedelta(
        days=config.ADMISSIONS_PAYMENT_DAYS
    )
    if not selection.user.admissions_requires_exam and config.NO_EXAM_USE_SCHEDULE:
        selection.payment_due_date = config.NO_EXAM_PAYMENTS_END
    selection.save()

    log_selection_event(
        selection,
        SelectionEvent.payment_data_reset
        if reset
        else SelectionEvent.payment_data_populated,
        data={
            "old-ticket-type": old_ticket_type,
            "new-ticket-type": ticket_type,
            "old-payment-value": old_value,
            "new-payment-value": value,
        },
        user=staff,
    )


def add_document(
    selection: Selection,
    document: SelectionDocument,
    document_type,
) -> None:
    logger.info("selection=%d: new document uploaded", selection.id)
    document = SelectionDocument.objects.create(
        selection=selection,
        doc=document,
        doc_type=document_type,
    )

    log_selection_event(
        selection,
        SelectionEvent.document_added,
        data={
            "doc-type": document.doc_type,
            "doc-location": document.doc.url,
        },
        user=selection.user,
    )


def add_note(selection, note, user=None):
    log_selection_event(
        selection, SelectionEvent.note_added, data={"note": note}, user=user
    )


def can_be_updated(selection: Selection) -> bool:
    return bool(
        config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS
        and payment_window_open(selection.user)
        and selection.payment_value is not None
        and selection.status
        in (SelectionStatus.SELECTED, SelectionStatus.TO_BE_ACCEPTED)
    )
