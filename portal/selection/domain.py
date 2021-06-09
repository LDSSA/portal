from .logs import SelectionEvent, log_selection_event
from .models import Selection
from .status import SelectionStatusType


class SelectionDomain:
    @staticmethod
    def create(user):
        return Selection.objects.get_or_create(user=user)[0]

    @staticmethod
    def get_status(selection):
        return SelectionStatusType(selection.status)

    @staticmethod
    def update_status(
        selection,
        status,
        *,
        draw_rank=None,
        user=None,
    ):
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
    def manual_update_status(selection, status, user, *, msg=""):
        old_status = SelectionDomain.get_status(selection)
        selection.status = status

        selection.save()

        log_selection_event(
            selection,
            SelectionEvent.status_updated,
            {"old-status": old_status, "new-status": status, "message": msg},
            user=user,
        )
