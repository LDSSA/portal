from logging import getLogger
from portal.users.models import TicketType, Gender
from typing import Iterable, Iterator, NamedTuple, Optional, Set, Tuple

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
    min_scholarships_quota: float
    min_female_quota: float
    max_company_quota: float


default_draw_params = DrawParams(
    number_of_seats=60, min_scholarships_quota=10/60, min_female_quota=0.35, max_company_quota=10/60
)


class DrawCounters:
    def __init__(self) -> None:
        self.total = 0
        self.female = 0
        self.scholarships = 0
        self.company = 0

    def update(self, selection: Selection) -> None:
        user = selection.user

        self.total += 1

        if user.gender == "female":
            self.female += 1

        if user.ticket_type == "scholarship":
            self.scholarships += 1

        if user.ticket_type == "company":
            self.company += 1


def must_pick_scholarship(params: DrawParams, counters: DrawCounters) -> bool:
    fraction_if_not_drawn = counters.scholarships / (
        counters.total + 1
    )
    return fraction_if_not_drawn < params.min_scholarships_quota


def must_pick_female(params: DrawParams, counters: DrawCounters) -> bool:
    fraction_if_not_drawn = counters.female / (
        counters.total + 1
    )
    return fraction_if_not_drawn < params.min_female_quota


def must_not_pick_company(params: DrawParams, counters: DrawCounters) -> bool:
    fraction_if_drawn = (counters.company + 1) / (
        counters.total + 1
    )
    return fraction_if_drawn >= params.max_company_quota


def get_draw_counters(candidates: Iterable[Selection]) -> DrawCounters:
    counters = DrawCounters()

    for candidate in candidates:
        counters.update(candidate)

    return counters


def iter_draw_constraints(
        params: DrawParams,
        counters: DrawCounters,
) -> Iterator[Tuple[Set[Gender], Set[TicketType]]]:
    # this function controls how we compute and loosen the draw constraints
    # loosening the constraints is required when we still need to draw
    # candidates and none matches the current criteria

    forbidden_genders: Set[Gender] = set()
    forbidden_ticket_types: Set[TicketType] = set()

    if must_pick_female(params, counters):
        forbidden_genders.update([Gender.male, Gender.other])

    if must_pick_scholarship(params, counters):
        forbidden_ticket_types.update([TicketType.regular, TicketType.student, TicketType.company])

    if must_not_pick_company(params, counters):
        forbidden_ticket_types.add(TicketType.company)

    def forget_none(fg: set[Gender], ftt: set[TicketType]) -> None:
        pass

    def forget_female_ratio(fg: set[Gender], ftt: set[TicketType]) -> None:
        fg.difference_update([Gender.male, Gender.other])

    def forget_company_ratio(fg: set[Gender], ftt: set[TicketType]) -> None:
        ftt.discard(TicketType.company)

    def forget_scholarship_ratio(fg: set[Gender], ftt: set[TicketType]) -> None:
        ftt.difference_update([TicketType.regular, TicketType.student, TicketType.company])

    for loosen_funcs in [
        (forget_none,),
        (forget_female_ratio,),
        (forget_company_ratio,),
        (forget_female_ratio, forget_company_ratio),
        (forget_scholarship_ratio,),
        (forget_scholarship_ratio, forget_female_ratio),
        (forget_scholarship_ratio, forget_company_ratio),
        (forget_scholarship_ratio, forget_female_ratio, forget_company_ratio,),
    ]:
        forbidden_genders_cp = forbidden_genders.copy()
        forbidden_ticket_types_cp = forbidden_ticket_types.copy()
        for loosen_func in loosen_funcs:
            loosen_func(forbidden_genders_cp, forbidden_ticket_types_cp)
        yield forbidden_genders_cp, forbidden_ticket_types_cp


def draw_next(
        params: DrawParams,
        counters: DrawCounters,
) -> Optional[Selection]:
    for fg, ftt in iter_draw_constraints(params, counters):
        q = SelectionQueries.draw_filter(list(fg), list(ftt))
        sel = SelectionQueries.random(q)
        if sel is not None:
            return sel

    return None


def draw(params: DrawParams) -> None:
    current_candidates = SelectionQueries.filter_by_status_in(
        [
            SelectionStatus.DRAWN,
            SelectionStatus.INTERVIEW,
            SelectionStatus.SELECTED,
            SelectionStatus.TO_BE_ACCEPTED,
            SelectionStatus.ACCEPTED,
        ]
    )

    counters = get_draw_counters(current_candidates)
    draw_rank = SelectionQueries.max_rank(current_candidates) + 1

    while counters.total != params.number_of_seats:
        selection = draw_next(params, counters)
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
