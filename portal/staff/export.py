from typing import Any, NamedTuple

from django.db.models import F

from portal.users.models import User


class ExportData(NamedTuple):
    headers: list[str]
    rows: list[dict[str, Any]]


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
        "profile_create_at": "created_at",
        "profile_updated_at": "updated_at",
        "name": "name",
        "profession": "profession",
        "gender": "gender",
        "ticket_type": "ticket_type",
        "company": "company",
        # selection
        "selection_create_at": "selection__created_at",
        "selection_updated_at": "selection__updated_at",
        "status": "selection__status",
        "payment_value": "selection__payment_value",
        "payment_ticket_type": "selection__ticket_type",
        "payment_due_date": "selection__payment_due_date",
    }

    rows = (
        User.objects.exclude(is_staff=True)
        .order_by("id")
        .values("id")
        .annotate(**{k: F(v) for k, v in headers.items()})
    )

    return ExportData(headers=["id", *[k for k, _ in headers.items()]], rows=rows)
