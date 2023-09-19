from logging import getLogger

from constance import config
from django.conf import settings

from portal.applications.domain import Domain as ApplicationDomain
from portal.applications.domain import (
    DomainException as ApplicationDomainException,
)
from portal.applications.domain import (
    DomainQueries as ApplicationDomainQueries,
)
from portal.admissions import emails
from portal.selection.domain import SelectionDomain
from portal.selection.queries import SelectionQueries
from portal.selection.status import SelectionStatus


logger = getLogger(__name__)


class EventsException(Exception):
    pass


class Events:
    @staticmethod
    def applications_are_over_sent_emails() -> int:
        return ApplicationDomainQueries.applications_with_sent_emails_count()

    @staticmethod
    def applications_are_over_total_emails() -> int:
        return ApplicationDomainQueries.applications_count()

    @staticmethod
    def trigger_applications_are_over() -> None:
        if config.PORTAL_STATUS == "admissions:applications":
            logger.error(
                "trying to trigger `applications over` event but applications are still open"
            )
            raise EventsException("Can't trigger `applications over` event")

        sent_count = 0
        q = ApplicationDomainQueries.all()
        for a in q:
            try:
                ApplicationDomain.application_over(a)
                sent_count += 1
            except ApplicationDomainException:
                pass  # means that email was already sent

            a.refresh_from_db()
            if a.application_over_email_sent == "passed":
                SelectionDomain.create(a.user)

        logger.info(f"sent {sent_count} `application_over` emails")

    @staticmethod
    def admissions_are_over_sent_emails() -> int:
        return SelectionQueries.filter_by_status_in(SelectionStatus.FINAL_STATUS).count()

    @staticmethod
    def admissions_are_over_total_emails() -> int:
        return SelectionQueries.get_all().count()

    @staticmethod
    def trigger_admissions_are_over() -> None:
        if config.PORTAL_STATUS == "admissions:applications":
            logger.error(
                "trying to trigger `admissions over` event but applications are still open"
            )
            raise EventsException("Can't trigger `admissions over` event (applications open)")

        if SelectionQueries.filter_by_status_in(
            [
                SelectionStatus.DRAWN,
                SelectionStatus.INTERVIEW,
                SelectionStatus.SELECTED,
                SelectionStatus.TO_BE_ACCEPTED,
            ]
        ).exists():
            logger.error("trying to trigger `admissions over` event but open selections exist")
            raise EventsException(
                "Can't trigger `admissions over` event (DRAWN, INTERVIEW, SELECTED, TO_BE_ACCEPTED exists)"
            )

        sent_count = 0
        for selection in SelectionQueries.get_all():
            selection_status = SelectionDomain.get_status(selection)
            if selection_status == SelectionStatus.ACCEPTED:
                selection.user.is_student = True
                selection.user.save()

            if selection_status == SelectionStatus.PASSED_TEST:
                # this user was never selected
                SelectionDomain.update_status(selection, SelectionStatus.NOT_SELECTED)
                emails.send_admissions_are_over_not_selected(
                    to_email=selection.user.email,
                    to_name=selection.user.name,
                )

            sent_count += 1

        logger.info(f"sent {sent_count} `admissions_over` emails")
