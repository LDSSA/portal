from enum import Enum
from logging import getLogger
from typing import Any

from portal.users.models import User

from .models import Selection, SelectionLogs

logger = getLogger(__name__)


class DomainExceptionError(Exception):
    pass


class SelectionEvent(Enum):
    status_updated = "[Status Updated]"
    payment_data_populated = "[Payment Data Populated]"
    payment_data_reset = "[Payment Data Reset]"
    document_added = "[Document Added]"
    note_added = "[Note Added]"


def log_selection_event(
    selection: Selection,
    event: SelectionEvent,
    data: dict[str, Any],
    *,
    user: User | None = None,
) -> None:
    data_s = "\n".join([f"{k}: {v}" for k, v in data.items()])
    msg = f"{event.value}\n{data_s}\n---\ntriggered by {user.email if user is not None else 'unknown'}"
    SelectionLogs.objects.create(selection=selection, event=event.name, message=msg)


def get_selection_logs(selection: Selection) -> list[dict[str, Any]]:
    return (
        SelectionLogs.objects.filter(selection=selection)
        .order_by("-created_at")
        .values("event", "message", "created_at")
    )
