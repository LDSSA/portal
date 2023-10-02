from django.test import TestCase  # noqa: D100
from profiles.models import Profile, ProfileGenders, ProfileTicketTypes
from users.models import User

from portal.selection.models import Selection
from portal.selection.queries import SelectionQueries
from portal.selection.select import select
from portal.selection.status import SelectionStatus


class TestSelect(TestCase):  # noqa: D101
    def test_select_to_selected(self) -> None:  # noqa: ANN101, D102
        for i in range(5):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(9):
            u = User.objects.create(email=f"drawn_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.DRAWN)

        select()

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.SELECTED]).count()
            == 9  # noqa: PLR2004
        )  # noqa: S101
        for selection in SelectionQueries.filter_by_status_in([SelectionStatus.SELECTED]):
            assert selection.ticket_type == ProfileTicketTypes.regular  # noqa: S101
            assert selection.payment_value == 250  # noqa: PLR2004, S101

    # def test_select_to_interview(self) -> None:
    #     for i in range(9):
    #         u = User.objects.create(email=f"female_user_{i}@amd.com")  # noqa: ERA001
    #         Profile.objects.create(user=u,
    #                                ticket_type=ProfileTicketTypes.company,  # noqa: ERA001
    #                                gender=ProfileGenders.female)
    #         Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)  # noqa: ERA001
    #
    #         u = User.objects.create(email=f"drawn_female_user_{i}@amd.com")  # noqa: ERA001
    #         Profile.objects.create(user=u,
    #                                ticket_type=ProfileTicketTypes.company,  # noqa: ERA001
    #                                gender=ProfileGenders.female)
    #         Selection.objects.create(user=u, status=SelectionStatus.DRAWN)  # noqa: ERA001
    #
    #     Domain.select()  # noqa: ERA001
    #
    #     self.assertEqual(filter_by_status_in([SelectionStatus.INTERVIEW]).count(), 9)  # noqa: ERA001
