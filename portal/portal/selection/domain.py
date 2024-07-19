from .logs import SelectionEvent, log_selection_event  # noqa: D100
from .models import Selection
from .status import SelectionStatusType


class SelectionDomain:  # noqa: D101
    @staticmethod
    def create(user):  # noqa: ANN001, ANN205, D102
        return Selection.objects.get_or_create(user=user)[0]

    @staticmethod
    def get_status(selection):  # noqa: ANN001, ANN205, D102
        return SelectionStatusType(selection.status)

    @staticmethod
    def update_status(  # noqa: ANN205, D102
        selection,  # noqa: ANN001
        status,  # noqa: ANN001
        *,
        draw_rank=None,  # noqa: ANN001
        user=None,  # noqa: ANN001
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
    def manual_update_status(selection, status, user, *, msg=""):  # noqa: ANN001, ANN205, D102
        old_status = SelectionDomain.get_status(selection)
        selection.status = status

        selection.save()

        log_selection_event(
            selection,
            SelectionEvent.status_updated,
            {"old-status": old_status, "new-status": status, "message": msg},
            user=user,
        )
