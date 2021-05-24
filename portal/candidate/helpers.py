from datetime import datetime, timezone
from typing import Any, Dict, Optional

from constance import config

from portal.selection.models import Selection
from portal.users.models import User


def applications_are_open() -> bool:
    return (
        datetime.now(timezone.utc)
        > config.ADMISSIONS_APPLICATIONS_OPENING_DATE
    )


def user_has_payment(user: User) -> bool:
    try:
        return user.selection.payment_value is not None
    except Selection.DoesNotExist:
        return False


def build_context(
    user: User, ctx: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    base_ctx = {
        "user_has_payment": user_has_payment(user),
        "user_accepted_coc": user.code_of_conduct_accepted,
        "scholarship_decided": user.applying_for_scholarship is not None,
        "user_has_profile": getattr(user, "profile", None) is not None,
        "applications_are_open": applications_are_open(),
    }
    ctx = ctx or {}

    return {**base_ctx, **ctx}