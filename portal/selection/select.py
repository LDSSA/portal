from logging import getLogger

from interface import interface
from profiles.models import ProfileTicketTypes

from .domain import SelectionDomain
from .models import Selection
from .payment import load_payment_data
from .queries import SelectionQueries
from .status import SelectionStatus

logger = getLogger(__name__)


def requires_interview(selection: Selection) -> bool:
    return selection.user.profile.ticket_type == ProfileTicketTypes.scholarship


def select() -> None:
    for selection in SelectionQueries.filter_by_status_in(
        [SelectionStatus.DRAWN]
    ):
        if requires_interview(selection):
            to_interview(selection)
        else:
            to_selected(selection)


def to_selected(selection: Selection) -> None:
    SelectionDomain.update_status(selection, SelectionStatus.SELECTED)
    load_payment_data(selection)

    payment_due_date = selection.payment_due_date.strftime("%Y-%m-%d")
    interface.email_client.send_selected_and_payment_details(
        to_email=selection.user.email,
        to_name=selection.user.profile.name,
        payment_value=selection.payment_value,
        payment_due_date=payment_due_date,
    )


def to_interview(selection: Selection) -> None:
    SelectionDomain.update_status(selection, SelectionStatus.INTERVIEW)
    interface.email_client.send_selected_interview_details(
        to_email=selection.user.email, to_name=selection.user.profile.name
    )
