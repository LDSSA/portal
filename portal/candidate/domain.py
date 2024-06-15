from typing import NamedTuple  # noqa: D100

import nbconvert
import nbformat

from portal.applications.domain import ApplicationStatus, SubmissionStatus
from portal.applications.domain import Domain as ApplicationsDomain
from portal.applications.models import Application, Challenge
from portal.selection.domain import SelectionDomain
from portal.selection.models import Selection
from portal.selection.status import SelectionStatusType
from portal.users.models import User


def notebook_to_html(nb):  # noqa: ANN001, ANN201, D103
    nb = nbformat.reads(nb, as_version=4)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_name = "classic"
    body, _ = html_exporter.from_notebook_node(nb)
    return body


class CandidateState(NamedTuple):  # noqa: D101
    accepted_coc: bool
    decided_scholarship: bool
    applying_for_scholarship: bool | None
    application_status: ApplicationStatus | None
    coding_test_status: SubmissionStatus | None
    slu01_status: SubmissionStatus | None
    slu02_status: SubmissionStatus | None
    slu03_status: SubmissionStatus | None
    selection_status: SelectionStatusType | None
    academy_type: str | None



class DomainExceptionError(Exception):  # noqa: D101
    pass


class Domain:  # noqa: D101
    @staticmethod
    def get_candidate_state(candidate: User) -> CandidateState:  # noqa: D102
        state = {}

        state["accepted_coc"] = candidate.code_of_conduct_accepted

        state["decided_scholarship"] = candidate.applying_for_scholarship is not None
        state["applying_for_scholarship"] = candidate.applying_for_scholarship
        state["academy_type"] = candidate.academy_type_preference

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
    def candidate_state_readable(  # noqa: D102
        candidate_state: CandidateState,
    ) -> dict[str, str]:
        return {
            k: k.replace("_", " ").title().replace("Slu", "SLU ")
            for k, _ in candidate_state._asdict().items()
        }
