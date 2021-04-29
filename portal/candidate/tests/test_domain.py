from datetime import datetime, timedelta

from django.test import TestCase

from applications.domain import ApplicationStatus, SubmissionStatus
from applications.models import Application
from candidate.domain import CandidateState, Domain
from interface import interface
from profiles.models import Profile
from selection.models import Selection
from selection.status import SelectionStatus
from users.models import User


class TestDomain(TestCase):
    def test_get_candidate_state_default(self) -> None:
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now() + timedelta(minutes=30)
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now() + timedelta(minutes=60)
        )

        candidate = User.objects.create(email="anon@adm.com")
        self.assertEqual(
            Domain.get_candidate_state(candidate),
            CandidateState(
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
            ),
        )

    def test_get_candidate_state(self) -> None:
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now() - timedelta(minutes=30)
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now() + timedelta(minutes=30)
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

        self.assertEqual(
            Domain.get_candidate_state(candidate),
            CandidateState(
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
            ),
        )

    def test_candidate_state_readable(self) -> None:
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
            Domain.get_candidate_state(
                User.objects.create(email="anon@adm.com")
            )
        )
        self.assertEqual(readable, expected)
