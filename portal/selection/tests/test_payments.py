from django.test import TestCase  # noqa: D100
from profiles.models import Profile, ProfileTicketTypes
from users.models import User

from portal.selection.models import Selection
from portal.selection.payment import load_payment_data
from portal.selection.status import SelectionStatus


class TestDomain(TestCase):  # noqa: D101
    def setUp(self) -> None:  # noqa: ANN101, D102, N802
        self.staff_user = User.objects.create_staff_user(
            email="staff@adm.com",
            password="secret",  # noqa: S106
        )  # noqa: S106

    def test_load_payment_data(self) -> None:  # noqa: ANN101, D102
        user = User.objects.create_user(email="user@adm.com", password="strong")  # noqa: S106
        Profile.objects.create(user=user, full_name="name", ticket_type=ProfileTicketTypes.regular)
        selection = Selection.objects.create(user=user, status=SelectionStatus.SELECTED)
        load_payment_data(selection)

        assert selection.ticket_type == ProfileTicketTypes.regular  # noqa: S101
        assert selection.payment_value == 250  # noqa: PLR2004, S101
        assert selection.status == SelectionStatus.SELECTED  # noqa: S101

    def test_create_payment_student(self) -> None:  # noqa: ANN101, D102
        user = User.objects.create_user(email="student@adm.com", password="strong")  # noqa: S106
        Profile.objects.create(user=user, full_name="name", ticket_type=ProfileTicketTypes.student)
        selection = Selection.objects.create(user=user, status=SelectionStatus.SELECTED)
        load_payment_data(selection)

        assert selection.ticket_type == ProfileTicketTypes.student  # noqa: S101
        assert selection.payment_value == 100  # noqa: PLR2004, S101
        assert selection.status == SelectionStatus.SELECTED  # noqa: S101

    def test_create_payment_company(self) -> None:  # noqa: ANN101, D102
        user = User.objects.create_user(email="company@adm.com", password="strong")  # noqa: S106
        Profile.objects.create(user=user, full_name="name", ticket_type=ProfileTicketTypes.company)
        selection = Selection.objects.create(user=user, status=SelectionStatus.SELECTED)
        load_payment_data(selection)

        assert selection.ticket_type == ProfileTicketTypes.company  # noqa: S101
        assert selection.payment_value == 1500  # noqa: PLR2004, S101
        assert selection.status == SelectionStatus.SELECTED  # noqa: S101

    #
    # def test_add_document_regular(self) -> None:
    #     user = User.objects.create_user(email="user@adm.com", password="strong")  # noqa: ERA001
    #     Profile.objects.create(user=user, full_name="name", ticket_type=ProfileTicketTypes.regular)  # noqa: ERA001
    #     selection = Selection.objects.create(user=user, status=SelectionStatus.SELECTED)  # noqa: ERA001
    #
    #     self.assertFalse(selection.has_payment_proof_document)  # noqa: ERA001
    #     self.assertFalse(payment.has_student_id_document)  # noqa: ERA001
    #     self.assertEqual(Document.objects.filter(payment=payment).count(), 0)  # noqa: ERA001
    #
    #     document = Document(doc_type="payment_proof", file_location="dummy")  # noqa: ERA001
    #     Domain.add_document(payment, document)  # noqa: ERA001
    #
    #     self.assertEqual(payment.status, "pending_verification")  # noqa: ERA001
    #     self.assertTrue(payment.has_payment_proof_document)  # noqa: ERA001
    #     self.assertFalse(payment.has_student_id_document)  # noqa: ERA001
    #     self.assertEqual(Document.objects.filter(payment=payment).count(), 1)  # noqa: ERA001
    #
    # def test_add_document_student(self) -> None:
    #     user = User.objects.create_user(email="user@adm.com", password="strong")  # noqa: ERA001
    #     profile = Profile.objects.create(user=user, full_name="name", ticket_type=ProfileTicketTypes.student)  # noqa: ERA001
    #     SelectedDomain.new_candidate(user)  # noqa: ERA001
    #     payment = Domain.create_payment(profile)  # noqa: ERA001
    #
    #     self.assertFalse(payment.has_payment_proof_document)  # noqa: ERA001
    #     self.assertFalse(payment.has_student_id_document)  # noqa: ERA001
    #     self.assertEqual(Document.objects.filter(payment=payment).count(), 0)  # noqa: ERA001
    #
    #     document = Document(doc_type="payment_proof", file_location="dummy")  # noqa: ERA001
    #     Domain.add_document(payment, document)  # noqa: ERA001
    #
    #     self.assertEqual(payment.status, "waiting_for_documents")  # noqa: ERA001
    #     self.assertTrue(payment.has_payment_proof_document)  # noqa: ERA001
    #     self.assertFalse(payment.has_student_id_document)  # noqa: ERA001
    #     self.assertEqual(Document.objects.filter(payment=payment).count(), 1)  # noqa: ERA001
    #
    #     document = Document(doc_type="student_id", file_location="dummy")  # noqa: ERA001
    #     Domain.add_document(payment, document)  # noqa: ERA001
    #
    #     self.assertEqual(payment.status, "pending_verification")  # noqa: ERA001
    #     self.assertTrue(payment.has_payment_proof_document)  # noqa: ERA001
    #     self.assertTrue(payment.has_student_id_document)  # noqa: ERA001
    #     self.assertEqual(Document.objects.filter(payment=payment).count(), 2)  # noqa: ERA001
