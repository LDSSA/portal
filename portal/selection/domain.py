from typing import Optional

from users.models import User

from .logs import SelectionEvent, log_selection_event
from .models import Selection
from .status import SelectionStatusType


class SelectionDomain:
    @staticmethod
    def create(user: User) -> Selection:
        return Selection.objects.create(user=user)

    @staticmethod
    def get_status(selection: Selection) -> SelectionStatusType:
        return SelectionStatusType(selection.status)

    @staticmethod
    def update_status(
        selection: Selection,
        status: SelectionStatusType,
        *,
        draw_rank: Optional[int] = None,
        user: Optional[User] = None
    ) -> None:
        old_status = SelectionDomain.get_status(selection)
        selection.status = status

        if draw_rank is not None:
            selection.draw_rank = draw_rank

        selection.save()

        log_selection_event(
            selection,
            SelectionEvent.status_updated,
            {
                "old-status": old_status,
                "new-status": status,
                "draw-rank": draw_rank,
            },
            user=user,
        )

    @staticmethod
    def manual_update_status(
        selection: Selection,
        status: SelectionStatusType,
        user: User,
        *,
        msg: str = ""
    ) -> None:
        old_status = SelectionDomain.get_status(selection)
        selection.status = status

        selection.save()

        log_selection_event(
            selection,
            SelectionEvent.status_updated,
            {"old-status": old_status, "new-status": status, "message": msg},
            user=user,
        )
