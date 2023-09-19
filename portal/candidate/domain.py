from typing import Dict, NamedTuple, Optional

import nbformat
import nbconvert

from portal.applications.domain import ApplicationStatus
from portal.applications.domain import Domain as ApplicationsDomain
from portal.applications.domain import SubmissionStatus
from portal.applications.models import Application, Challenge
from portal.selection.domain import SelectionDomain
from portal.selection.models import Selection
from portal.selection.status import SelectionStatusType
from portal.users.models import User


def notebook_to_html(nb):
    nb = nbformat.reads(nb, as_version=4)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_name = "classic"
    body, _ = html_exporter.from_notebook_node(nb)
    return body


class CandidateState(NamedTuple):
    accepted_coc: bool
    decided_scholarship: bool
    applying_for_scholarship: Optional[bool]
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

        state["accepted_coc"] = candidate.code_of_conduct_accepted

        state["decided_scholarship"] = candidate.applying_for_scholarship is not None
        state["applying_for_scholarship"] = candidate.applying_for_scholarship

        application, _ = Application.objects.get_or_create(user=candidate)
        status = ApplicationsDomain.get_application_detailed_status(application)
        state["application_status"] = status["application"]
        state["coding_test_status"] = status[Challenge.objects.get(code="coding_test").code]
        state["slu01_status"] = status[Challenge.objects.get(code="slu01").code]
        state["slu02_status"] = status[Challenge.objects.get(code="slu02").code]
        state["slu03_status"] = status[Challenge.objects.get(code="slu03").code]

        try:
            state["selection_status"] = SelectionDomain.get_status(candidate.selection)

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
