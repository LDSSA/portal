from django.test import TestCase

from profiles.models import Profile, ProfileGenders, ProfileTicketTypes
from users.models import User

from ..models import Selection
from ..queries import SelectionQueries
from ..select import select
from ..status import SelectionStatus


class TestSelect(TestCase):
    def test_select_to_selected(self) -> None:
        for i in range(5):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(
                user=u, status=SelectionStatus.PASSED_TEST
            )

        for i in range(9):
            u = User.objects.create(email=f"drawn_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.DRAWN)

        select()

        self.assertEqual(
            SelectionQueries.filter_by_status_in(
                [SelectionStatus.SELECTED]
            ).count(),
            9,
        )
        for selection in SelectionQueries.filter_by_status_in(
            [SelectionStatus.SELECTED]
        ):
            self.assertEqual(selection.ticket_type, ProfileTicketTypes.regular)
            self.assertEqual(selection.payment_value, 250)

    # def test_select_to_interview(self) -> None:
    #     for i in range(9):
    #         u = User.objects.create(email=f"female_user_{i}@amd.com")
    #         Profile.objects.create(user=u, ticket_type=ProfileTicketTypes.company, gender=ProfileGenders.female)
    #         Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)
    #
    #         u = User.objects.create(email=f"drawn_female_user_{i}@amd.com")
    #         Profile.objects.create(user=u, ticket_type=ProfileTicketTypes.company, gender=ProfileGenders.female)
    #         Selection.objects.create(user=u, status=SelectionStatus.DRAWN)
    #
    #     Domain.select()
    #
    #     self.assertEqual(filter_by_status_in([SelectionStatus.INTERVIEW]).count(), 9)
