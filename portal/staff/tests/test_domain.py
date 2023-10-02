from datetime import datetime, timedelta  # noqa: D100

import pytest
from applications.models import Application, Submission, SubmissionTypes
from dateutil import gettz
from django.test import TestCase
from interface import interface
from profiles.models import Profile
from selection.domain import SelectionDomain
from selection.queries import SelectionQueries
from selection.status import SelectionStatus
from staff.domain import Events, EventsExceptionError
from users.models import User

LISBON_TZ = gettz("Europe/Lisbon")


class TestEvents(TestCase):  # noqa: D101
    def setUp(self) -> None:  # noqa: ANN101, D102, N802
        self.aod = datetime.now(LISBON_TZ) - timedelta(minutes=30)
        self.acd = datetime.now(LISBON_TZ) + timedelta(minutes=30)
        interface.feature_flag_client.set_applications_opening_date(self.aod)
        interface.feature_flag_client.set_applications_closing_date(self.acd)

    def test_trigger_applications_are_over_exception(self) -> None:  # noqa: ANN101, D102
        # because applications are not closed
        with pytest.raises(EventsExceptionError):
            Events.trigger_applications_are_over()

    def test_trigger_applications_are_over(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            self.aod - timedelta(minutes=60),
        )
        interface.feature_flag_client.set_applications_closing_date(
            self.acd - timedelta(minutes=60),
        )

        u1 = User.objects.create(email="u1@test.com")
        Profile.objects.create(user=u1)
        a1 = Application.objects.create(user=u1)

        u2 = User.objects.create(email="u2@test.com")
        Profile.objects.create(user=u2)
        a2 = Application.objects.create(user=u2)

        u3 = User.objects.create(email="u3@test.com")
        Profile.objects.create(user=u3)
        a3 = Application.objects.create(user=u3)

        u4 = User.objects.create(email="u4@test.com")
        Profile.objects.create(user=u4)
        a4 = Application.objects.create(user=u4)

        Submission.objects.create(
            application=a4,
            score=99,
            submission_type=SubmissionTypes.coding_test.uname,
        )
        Submission.objects.create(
            application=a4,
            score=99,
            submission_type=SubmissionTypes.slu01.uname,
        )
        Submission.objects.create(
            application=a4,
            score=99,
            submission_type=SubmissionTypes.slu02.uname,
        )
        Submission.objects.create(
            application=a4,
            score=99,
            submission_type=SubmissionTypes.slu03.uname,
        )

        a5 = Application.objects.create(
            user=User.objects.create(email="a5@test.com"),
            application_over_email_sent="passed",
        )

        assert Events.applications_are_over_total_emails() == 5  # noqa: PLR2004, S101
        assert Events.applications_are_over_sent_emails() == 1  # noqa: S101

        assert a1.application_over_email_sent is None  # noqa: S101
        assert a2.application_over_email_sent is None  # noqa: S101
        assert a3.application_over_email_sent is None  # noqa: S101
        assert a4.application_over_email_sent is None  # noqa: S101
        assert a5.application_over_email_sent == "passed"  # noqa: S101

        Events.trigger_applications_are_over()

        assert Events.applications_are_over_total_emails() == 5  # noqa: PLR2004, S101
        assert Events.applications_are_over_sent_emails() == 5  # noqa: PLR2004, S101

        a1.refresh_from_db()
        assert a1.application_over_email_sent == "failed"  # noqa: S101
        a2.refresh_from_db()
        assert a2.application_over_email_sent == "failed"  # noqa: S101
        a3.refresh_from_db()
        assert a3.application_over_email_sent == "failed"  # noqa: S101
        a4.refresh_from_db()
        assert a4.application_over_email_sent == "passed"  # noqa: S101
        a5.refresh_from_db()
        assert a5.application_over_email_sent == "passed"  # noqa: S101

    def test_trigger_admissions_are_over_exception(self) -> None:  # noqa: ANN101, D102
        # because applications are not closed
        with pytest.raises(EventsExceptionError):
            Events.trigger_admissions_are_over()

        interface.feature_flag_client.set_applications_opening_date(
            self.aod - timedelta(minutes=60),
        )
        interface.feature_flag_client.set_applications_closing_date(
            self.acd - timedelta(minutes=60),
        )

        selection = SelectionDomain.create(user=User.objects.create(email="u1@test.com"))
        SelectionDomain.update_status(selection, SelectionStatus.DRAWN)

        # because the is a drawn selection
        with pytest.raises(EventsExceptionError):
            Events.trigger_admissions_are_over()

        SelectionDomain.update_status(selection, SelectionStatus.INTERVIEW)

        # because the is a interview selection
        with pytest.raises(EventsExceptionError):
            Events.trigger_admissions_are_over()

        SelectionDomain.update_status(selection, SelectionStatus.SELECTED)

        # because the is a selected selection
        with pytest.raises(EventsExceptionError):
            Events.trigger_admissions_are_over()

        SelectionDomain.update_status(selection, SelectionStatus.TO_BE_ACCEPTED)

        # because the is a to_be_accepted selection
        with pytest.raises(EventsExceptionError):
            Events.trigger_admissions_are_over()

    def test_trigger_admissions_are_over(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            self.aod - timedelta(minutes=60),
        )
        interface.feature_flag_client.set_applications_closing_date(
            self.acd - timedelta(minutes=60),
        )

        u1 = User.objects.create(email="u1@test.com")
        Profile.objects.create(user=u1)
        SelectionDomain.update_status(SelectionDomain.create(user=u1), SelectionStatus.PASSED_TEST)

        u2 = User.objects.create(email="u2@test.com")
        Profile.objects.create(user=u2)
        SelectionDomain.update_status(SelectionDomain.create(user=u2), SelectionStatus.ACCEPTED)

        u3 = User.objects.create(email="u3@test.com")
        Profile.objects.create(user=u3)
        SelectionDomain.update_status(SelectionDomain.create(user=u3), SelectionStatus.REJECTED)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.PASSED_TEST]).count() == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.ACCEPTED]).count() == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.REJECTED]).count() == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.NOT_SELECTED]).count() == 0
        )  # noqa: S101

        Events.trigger_admissions_are_over()

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.PASSED_TEST]).count() == 0
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.ACCEPTED]).count() == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.REJECTED]).count() == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.NOT_SELECTED]).count() == 1
        )  # noqa: S101
