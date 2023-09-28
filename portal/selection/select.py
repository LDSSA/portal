from logging import getLogger  # noqa: D100

from portal.admissions import emails
from portal.users.models import TicketType

from .domain import SelectionDomain
from .payment import load_payment_data
from .queries import SelectionQueries
from .status import SelectionStatus

logger = getLogger(__name__)


def requires_interview(selection):  # noqa: D103
    return selection.user.ticket_type == TicketType.scholarship


def select() -> None:  # noqa: D103
    for selection in SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]):
        if requires_interview(selection):
            to_interview(selection)
        else:
            to_selected(selection)


def to_selected(selection):  # noqa: D103
    SelectionDomain.update_status(selection, SelectionStatus.SELECTED)
    load_payment_data(selection)

    payment_due_date = selection.payment_due_date.strftime("%Y-%m-%d")
    emails.send_selected_and_payment_details(
        to_email=selection.user.email,
        to_name=selection.user.name,
        payment_value=selection.payment_value,
        payment_due_date=payment_due_date,
    )


def to_interview(selection):  # noqa: D103
    SelectionDomain.update_status(selection, SelectionStatus.INTERVIEW)
    emails.send_selected_interview_details(
        to_email=selection.user.email, to_name=selection.user.name
    )
