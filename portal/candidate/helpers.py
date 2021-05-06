from datetime import datetime
from typing import Any, Dict, Optional

from interface import interface
from selection.models import Selection
from users.models import User


def applications_are_open() -> bool:
    return (
        datetime.now()
        > interface.feature_flag_client.get_applications_opening_date()
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
        "user_confirmed_email": user.email_confirmed,
        "user_accepted_coc": user.code_of_conduct_accepted,
        "scholarship_decided": user.applying_for_scholarship is not None,
        "user_has_profile": getattr(user, "profile", None) is not None,
        "applications_are_open": applications_are_open(),
    }
    ctx = ctx or {}

    return {**base_ctx, **ctx}
