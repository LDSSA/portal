from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Optional


from .domain import SelectionDomain
from .logs import SelectionEvent, log_selection_event
from .models import Selection, SelectionDocument
from .status import SelectionStatus

logger = getLogger(__name__)


PRICE_TABLE = {
    "student": 100,
    "regular": 250,
    "company": 1500,
    "scholarship": 20,
}


class PaymentException(Exception):
    pass


def load_payment_data(selection, staff=None):
    old_ticket_type = selection.ticket_type
    old_value = selection.payment_value

    ticket_type = selection.user.ticket_type
    value = PRICE_TABLE[ticket_type]

    selection.ticket_type = ticket_type
    selection.payment_value = value
    selection.payment_due_date = datetime.now(timezone.utc) + timedelta(hours=48)
    selection.save()

    log_selection_event(
        selection,
        SelectionEvent.payment_data_populated,
        data={
            "old-ticket-type": old_ticket_type,
            "new-ticket-type": ticket_type,
            "old-payment-value": old_value,
            "new-payment-value": value,
        },
        user=staff,
    )


def add_document(selection: Selection, document: SelectionDocument, document_type) -> None:
    logger.info(f"selection={selection.id}: new document uploaded")
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
    log_selection_event(selection, SelectionEvent.note_added, data={"note": note}, user=user)


def can_be_updated(selection: Selection) -> bool:
    return SelectionDomain.get_status(selection) not in SelectionStatus.FINAL_STATUS
