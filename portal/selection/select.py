from logging import getLogger

from django.conf import settings

from .domain import SelectionDomain
from .models import Selection
from .payment import load_payment_data
from .queries import SelectionQueries
from .status import SelectionStatus

logger = getLogger(__name__)


def requires_interview(selection):
    return selection.user.profile.ticket_type == ProfileTicketTypes.scholarship


def select() -> None:
    for selection in SelectionQueries.filter_by_status_in(
        [SelectionStatus.DRAWN]
    ):
        if requires_interview(selection):
            to_interview(selection)
        else:
            to_selected(selection)


def to_selected(selection):
    SelectionDomain.update_status(selection, SelectionStatus.SELECTED)
    load_payment_data(selection)

    payment_due_date = selection.payment_due_date.strftime("%Y-%m-%d")
    client = settings.EMAIL_ELASTICMAIL_CLIENT()
    client.email_client.send_selected_and_payment_details(
        to_email=selection.user.email,
        to_name=selection.user.profile.name,
        payment_value=selection.payment_value,
        payment_due_date=payment_due_date,
    )


def to_interview(selection):
    SelectionDomain.update_status(selection, SelectionStatus.INTERVIEW)
    client = settings.EMAIL_ELASTICMAIL_CLIENT()
    client.email_client.send_selected_interview_details(
        to_email=selection.user.email, to_name=selection.user.profile.name
    )
