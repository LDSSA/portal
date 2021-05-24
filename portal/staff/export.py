from django.db.models import F

from users.models import User
import csv
from typing import Any, Dict, List, NamedTuple


class ExportData(NamedTuple):
    headers: List[str]
    rows: List[Dict[str, Any]]


def get_all_candidates() -> ExportData:
    user = User
    user.applying_for_scholarship

    headers = {
        # profile
        "create_at": "created_at",
        "updated_at": "updated_at",
        "email": "email",
        "coc_accepted": "code_of_conduct_accepted",
        "applying_for_scholarship": "applying_for_scholarship",
        # profile
        "profile_create_at": "profile__created_at",
        "profile_updated_at": "profile__updated_at",
        "name": "profile__full_name",
        "profession": "profile__profession",
        "gender": "profile__gender",
        "ticket_type": "profile__ticket_type",
        "company": "profile__company",
        # selection
        "selection_create_at": "selection__created_at",
        "selection_updated_at": "selection__updated_at",
        "status": "selection__status",
        "payment_value": "selection__payment_value",
        "payment_ticket_type": "selection__ticket_type",
        "payment_due_date": "selection__payment_due_date",
    }

    rows = (
        User.objects
        .exclude(is_staff=True)
        .order_by("id")
        .values("id")
        .annotate(**{k: F(v) for k, v in headers.items()})
    )

    return ExportData(
        headers=["id", *[k for k, _ in headers.items()]], rows=rows
    )
