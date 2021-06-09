from logging import getLogger
from portal.users.models import TicketType, Gender
from typing import Iterable, List, NamedTuple, Optional

from .domain import SelectionDomain
from .models import Selection
from .queries import SelectionQueries
from .status import SelectionStatus

logger = getLogger(__name__)


class DrawException(Exception):
    pass


class DrawParams(NamedTuple):
    # number of desired "currently" selected
    number_of_seats: int
    min_female_quota: float
    max_company_quota: float


default_draw_params = DrawParams(
    number_of_seats=50, min_female_quota=0.35, max_company_quota=0.2
)


class DrawCounters:
    def __init__(self) -> None:
        self.total = 0
        self.female = 0
        self.company = 0

    def update(self, selection: Selection) -> None:
        user = selection.user

        self.total += 1

        if user.gender == "female":
            self.female += 1

        if user.ticket_type == "company":
            self.company += 1


def must_pick_female(params: DrawParams, counters: DrawCounters) -> bool:
    female_fraction_if_non_female_drawn = counters.female / (
        counters.total + 1
    )
    return female_fraction_if_non_female_drawn < params.min_female_quota


def must_not_pick_company(params: DrawParams, counters: DrawCounters) -> bool:
    company_fraction_if_company_drawn = (counters.company + 1) / (
        counters.total + 1
    )
    return company_fraction_if_company_drawn >= params.max_company_quota


def get_draw_counters(candidates: Iterable[Selection]) -> DrawCounters:
    counters = DrawCounters()

    for candidate in candidates:
        counters.update(candidate)

    return counters


def draw_next(
    scholarships: bool,
    forbidden_genders: List[str],
    forbidden_ticket_types: List[str],
) -> Optional[Selection]:
    if not scholarships:
        q = SelectionQueries.draw_filter(
            forbidden_genders, forbidden_ticket_types
        ).exclude(user__ticket_type=TicketType.scholarship)
    else:
        q = SelectionQueries.draw_filter(
            forbidden_genders, forbidden_ticket_types
        ).filter(user__ticket_type=TicketType.scholarship)

    return SelectionQueries.random(q)


def draw(params: DrawParams, *, scholarships: bool) -> None:
    current_candidates = SelectionQueries.filter_by_status_in(
        [
            SelectionStatus.DRAWN,
            SelectionStatus.INTERVIEW,
            SelectionStatus.SELECTED,
            SelectionStatus.TO_BE_ACCEPTED,
            SelectionStatus.ACCEPTED,
        ]
    )
    if scholarships:
        current_candidates = current_candidates.filter(
            user__ticket_type=TicketType.scholarship
        )
    else:
        current_candidates = current_candidates.exclude(
            user__ticket_type=TicketType.scholarship
        )

    counters = get_draw_counters(current_candidates)
    draw_rank = SelectionQueries.max_rank(current_candidates) + 1

    while counters.total != params.number_of_seats:
        forbidden_genders = (
            [Gender.male, Gender.other]
            if must_pick_female(params, counters)
            else []
        )
        forbidden_ticket_types = (
            [TicketType.company]
            if must_not_pick_company(params, counters)
            else []
        )

        selection = draw_next(
            scholarships, forbidden_genders, forbidden_ticket_types
        )
        if selection is None:
            selection = draw_next(scholarships, [], forbidden_ticket_types)
        if selection is None:
            selection = draw_next(scholarships, forbidden_genders, [])
        if selection is None:
            selection = draw_next(scholarships, [], [])
        if selection is None:
            selection = draw_next(False, [], [])
        if selection is None:
            # no more suitable candidates
            break

        SelectionDomain.update_status(
            selection, SelectionStatus.DRAWN, draw_rank=draw_rank
        )
        counters.update(selection)
        draw_rank += 1


def reject_draw(selection: Selection) -> None:
    current_status = SelectionDomain.get_status(selection)
    if current_status != SelectionStatus.DRAWN:
        raise DrawException(
            f"Can't reject draw for candidate in status {current_status}."
        )

    SelectionDomain.update_status(selection, SelectionStatus.PASSED_TEST)
