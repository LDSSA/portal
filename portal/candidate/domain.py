from typing import Dict, NamedTuple, Optional

from applications.domain import ApplicationStatus
from applications.domain import Domain as ApplicationsDomain
from applications.domain import SubmissionStatus
from applications.models import Application, SubmissionTypes
from profiles.models import Profile
from selection.domain import SelectionDomain
from selection.models import Selection
from selection.status import SelectionStatusType
from users.models import User


class CandidateState(NamedTuple):
    confirmed_email: bool
    accepted_coc: bool
    decided_scholarship: bool
    applying_for_scholarship: Optional[bool]
    created_profile: bool
    application_status: Optional[ApplicationStatus]
    coding_test_status: Optional[SubmissionStatus]
    slu01_status: Optional[SubmissionStatus]
    slu02_status: Optional[SubmissionStatus]
    slu03_status: Optional[SubmissionStatus]
    selection_status: Optional[SelectionStatusType]


class DomainException(Exception):
    pass


class Domain:
    @staticmethod
    def get_candidate_state(candidate: User) -> CandidateState:
        state = {}

        state["confirmed_email"] = candidate.email_confirmed

        state["accepted_coc"] = candidate.code_of_conduct_accepted

        state["decided_scholarship"] = (
            candidate.applying_for_scholarship is not None
        )
        state["applying_for_scholarship"] = candidate.applying_for_scholarship

        try:
            _ = candidate.profile
            state["created_profile"] = True
        except Profile.DoesNotExist:
            state["created_profile"] = False

        application, _ = Application.objects.get_or_create(user=candidate)
        status = ApplicationsDomain.get_application_detailed_status(
            application
        )
        state["application_status"] = status["application"]
        state["coding_test_status"] = status[SubmissionTypes.coding_test.uname]
        state["slu01_status"] = status[SubmissionTypes.slu01.uname]
        state["slu02_status"] = status[SubmissionTypes.slu02.uname]
        state["slu03_status"] = status[SubmissionTypes.slu03.uname]

        try:
            state["selection_status"] = SelectionDomain.get_status(
                candidate.selection
            )

        except Selection.DoesNotExist:
            state["selection_status"] = None

        return CandidateState(**state)

    @staticmethod
    def candidate_state_readable(
        candidate_state: CandidateState,
    ) -> Dict[str, str]:
        return {
            k: k.replace("_", " ").title().replace("Slu", "SLU ")
            for k, _ in candidate_state._asdict().items()
        }
