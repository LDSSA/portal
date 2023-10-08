from datetime import datetime, timedelta, timezone  # noqa: D100

from django.test import TestCase

from portal.applications.domain import ApplicationStatus, SubmissionStatus
from portal.applications.models import Application
from portal.candidate.domain import CandidateState, Domain
from portal.interface import interface
from portal.profiles.models import Profile
from portal.selection.models import Selection
from portal.selection.status import SelectionStatus
from portal.users.models import User

LISBON_TZ = timezone.utc


class TestDomain(TestCase):  # noqa: D101
    def test_get_candidate_state_default(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=60),
        )

        candidate = User.objects.create(email="anon@adm.com")
        assert Domain.get_candidate_state(candidate) == CandidateState(  # noqa: S101
            confirmed_email=False,
            created_profile=False,
            accepted_coc=False,
            decided_scholarship=False,
            applying_for_scholarship=None,
            application_status=ApplicationStatus.not_started,
            coding_test_status=SubmissionStatus.not_started,
            slu01_status=SubmissionStatus.not_started,
            slu02_status=SubmissionStatus.not_started,
            slu03_status=SubmissionStatus.not_started,
            selection_status=None,
        )  # noqa: S101

    def test_get_candidate_state(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        candidate = User.objects.create(
            email="candidate@adm.com",
            email_confirmed=True,
            code_of_conduct_accepted=True,
            applying_for_scholarship=True,
        )
        Profile.objects.create(user=candidate)
        Application.objects.create(user=candidate)
        Selection.objects.create(user=candidate)

        assert Domain.get_candidate_state(candidate) == CandidateState(  # noqa: S101
            confirmed_email=True,
            created_profile=True,
            accepted_coc=True,
            decided_scholarship=True,
            applying_for_scholarship=True,
            application_status=ApplicationStatus.ongoing,
            coding_test_status=SubmissionStatus.not_started,
            slu01_status=SubmissionStatus.ongoing,
            slu02_status=SubmissionStatus.ongoing,
            slu03_status=SubmissionStatus.ongoing,
            selection_status=SelectionStatus.PASSED_TEST,
        )  # noqa: S101

    def test_candidate_state_readable(self) -> None:  # noqa: ANN101, D102
        expected = {
            "confirmed_email": "Confirmed Email",
            "accepted_coc": "Accepted Coc",
            "decided_scholarship": "Decided Scholarship",
            "applying_for_scholarship": "Applying For Scholarship",
            "created_profile": "Created Profile",
            "application_status": "Application Status",
            "coding_test_status": "Coding Test Status",
            "slu01_status": "SLU 01 Status",
            "slu02_status": "SLU 02 Status",
            "slu03_status": "SLU 03 Status",
            "selection_status": "Selection Status",
        }

        readable = Domain.candidate_state_readable(
            Domain.get_candidate_state(User.objects.create(email="anon@adm.com")),
        )
        assert readable == expected  # noqa: S101
