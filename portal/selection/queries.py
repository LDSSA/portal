from django.db.models import Max  # noqa: D100

from portal.users.models import Gender, TicketType

from .models import Selection, SelectionDocument
from .status import SelectionStatus, SelectionStatusType


class SelectionQueries:  # noqa: D101
    @staticmethod
    def get_all():  # noqa: ANN205, D102
        return Selection.objects.all()

    @staticmethod
    def filter_by_status_in(  # noqa: ANN205, D102
        status_list: list[SelectionStatusType],
    ):
        return Selection.objects.filter(status__in=status_list)

    @staticmethod
    def draw_filter(  # noqa: ANN205, D102
        forbidden_genders: list[Gender],
        forbidden_ticket_types: list[TicketType],
    ):
        return (
            Selection.objects.filter(status=SelectionStatus.PASSED_TEST)
            .exclude(user__gender__in=forbidden_genders)
            .exclude(user__ticket_type__in=forbidden_ticket_types)
        )

    @staticmethod
    def random(q):  # noqa: ANN001, ANN205, D102
        return q.order_by("?").first()

    @staticmethod
    def max_rank(q):  # noqa: ANN001, ANN205, D102
        return q.aggregate(Max("draw_rank"))["draw_rank__max"] or 0

    @staticmethod
    def scholarships(q):  # noqa: ANN001, ANN205, D102
        return q.filter(user__ticket_type=TicketType.scholarship)

    @staticmethod
    def no_scholarships(q):  # noqa: ANN001, ANN205, D102
        return q.exclude(user__ticket_type=TicketType.scholarship)


class SelectionDocumentQueries:  # noqa: D101
    @staticmethod
    def get_payment_proof_documents(  # noqa: ANN205, D102
        selection,  # noqa: ANN001
    ):
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="payment_proof")
            .order_by("-updated_at")
        )

    @staticmethod
    def get_student_id_documents(  # noqa: ANN205, D102
        selection,  # noqa: ANN001
    ):
        return (
            SelectionDocument.objects.filter(selection=selection)
            .filter(doc_type="student_id")
            .order_by("-updated_at")
        )
