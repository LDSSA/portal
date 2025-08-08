from logging import getLogger
from constance import config
from portal.admissions import emails
from portal.applications.domain import (
    DomainQueries as ApplicationDomainQueries,
)
from portal.selection.domain import SelectionDomain
from portal.selection.queries import SelectionQueries
from portal.selection.status import SelectionStatus

logger = getLogger(__name__)


class EventsExceptionError(Exception):
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
        if config.PORTAL_STATUS != "admissions:selection":
            logger.error(
                "trying to trigger `applications over` event but portal is not in selection status",
            )
            msg = "Can't trigger `applications over` event, portal status has to be admissions:selection"
            raise EventsExceptionError(msg)

        sent_count = 0
        q = ApplicationDomainQueries.all()
        for a in q:
            # this should be removed later
            if a.application_over_email_sent = 'failed':
                 a.application_over_email_sent = None
                 a.save()
            # up to here
            '''
            try:
                ApplicationDomain.application_over(a)
                sent_count += 1
            except ApplicationDomainExceptionError:
                pass  # means that email was already sent
            
            
            a.refresh_from_db()
            if a.application_over_email_sent == "passed":
                SelectionDomain.create(a.user)
            '''

            logger.info(a.application_over_email_sent)

        logger.info("sent %d `application_over` emails", sent_count)

    @staticmethod
    def admissions_are_over_sent_emails() -> int:
        return SelectionQueries.filter_by_status_in(
            SelectionStatus.FINAL_STATUS
        ).count()

    @staticmethod
    def admissions_are_over_total_emails() -> int:
        return SelectionQueries.get_all().count()

    @staticmethod
    def trigger_admissions_are_over() -> None:
        if config.PORTAL_STATUS == "admissions:applications":
            logger.error(
                "trying to trigger `admissions over` event but applications are still open",
            )
            msg = "Can't trigger `admissions over` event (applications open)"
            raise EventsExceptionError(msg)

        if SelectionQueries.filter_by_status_in(
            [
                SelectionStatus.DRAWN,
                SelectionStatus.INTERVIEW,
                SelectionStatus.SELECTED,
                SelectionStatus.TO_BE_ACCEPTED,
            ],
        ).exists():
            logger.error(
                "trying to trigger `admissions over` event but open selections exist"
            )
            msg = "Can't trigger `admissions over` event (DRAWN, INTERVIEW, SELECTED, TO_BE_ACCEPTED exists)"
            raise EventsExceptionError(
                msg,
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

        logger.info("sent %d `admissions_over` emails", sent_count)
