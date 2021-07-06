from typing import List

from django.db.models import Max


from portal.users.models import Gender, TicketType
from .models import Selection, SelectionDocument
from .status import SelectionStatus, SelectionStatusType


class SelectionQueries:
    @staticmethod
    def get_all():
        return Selection.objects.all()

    @staticmethod
    def filter_by_status_in(
        status_list: List[SelectionStatusType],
    ):
        return Selection.objects.filter(status__in=status_list)

    @staticmethod
    def draw_filter(
        forbidden_genders: List[Gender], forbidden_ticket_types: List[TicketType]
    ):
        return (
            Selection.objects.filter(status=SelectionStatus.PASSED_TEST)
            .exclude(user__gender__in=forbidden_genders)
            .exclude(user__ticket_type__in=forbidden_ticket_types)
        )

    @staticmethod
    def random(q):
        return q.order_by("?").first()

    @staticmethod
    def max_rank(q):
        return q.aggregate(Max("draw_rank"))["draw_rank__max"] or 0

    @staticmethod
    def scholarships(q):
        return q.filter(user__ticket_type=TicketType.scholarship)

    @staticmethod
    def no_scholarships(q):
        return q.exclude(user__ticket_type=TicketType.scholarship)


class SelectionDocumentQueries:
    @staticmethod
    def get_payment_proof_documents(
        selection,
    ):
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="payment_proof")
            .order_by("-updated_at")
        )

    @staticmethod
    def get_student_id_documents(
        selection,
    ):
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="student_id")
            .order_by("-updated_at")
        )
