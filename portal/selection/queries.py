from typing import List, Optional

from django.db.models import Max

from custom_typing.queryset import QuerySet
from profiles.models import ProfileTicketTypes

from .models import Selection, SelectionDocument
from .status import SelectionStatus, SelectionStatusType

SelectionQuerySet = QuerySet[Selection]
SelectionDocumentQuerySet = QuerySet[SelectionDocument]


class SelectionQueries:
    @staticmethod
    def get_all() -> SelectionQuerySet:
        return Selection.objects.all()

    @staticmethod
    def filter_by_status_in(
        status_list: List[SelectionStatusType],
    ) -> SelectionQuerySet:
        return Selection.objects.filter(status__in=status_list)

    @staticmethod
    def draw_filter(
        forbidden_genders: List[str], forbidden_ticket_types: List[str]
    ) -> SelectionQuerySet:
        return (
            Selection.objects.filter(status=SelectionStatus.PASSED_TEST)
            .exclude(user__profile__gender__in=forbidden_genders)
            .exclude(user__profile__ticket_type__in=forbidden_ticket_types)
        )

    @staticmethod
    def random(q: SelectionQuerySet) -> Optional[Selection]:
        return q.order_by("?").first()

    @staticmethod
    def max_rank(q: SelectionQuerySet) -> int:
        return q.aggregate(Max("draw_rank"))["draw_rank__max"] or 0

    @staticmethod
    def scholarships(q: SelectionQuerySet) -> SelectionQuerySet:
        return q.filter(
            user__profile__ticket_type=ProfileTicketTypes.scholarship
        )

    @staticmethod
    def no_scholarships(q: SelectionQuerySet) -> SelectionQuerySet:
        return q.exclude(
            user__profile__ticket_type=ProfileTicketTypes.scholarship
        )


class SelectionDocumentQueries:
    @staticmethod
    def get_payment_proof_documents(
        selection: Selection,
    ) -> SelectionDocumentQuerySet:
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="payment_proof")
            .order_by("-updated_at")
        )

    @staticmethod
    def get_student_id_documents(
        selection: Selection,
    ) -> SelectionDocumentQuerySet:
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="student_id")
            .order_by("-updated_at")
        )
