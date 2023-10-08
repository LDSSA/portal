import pytest  # noqa: D100
from django.test import TestCase  # noqa: D100
from profiles.models import Profile, ProfileGenders, ProfileTicketTypes
from users.models import User

from portal.selection.domain import SelectionDomain
from portal.selection.draw import (
    DrawCounters,
    DrawExceptionError,
    DrawParams,
    draw,
    must_not_pick_company,
    must_pick_female,
    reject_draw,
)
from portal.selection.models import Selection
from portal.selection.queries import SelectionQueries
from portal.selection.status import SelectionStatus


class TestDraw(TestCase):  # noqa: D101
    def test_must_pick_female(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=50, min_female_quota=0.35, max_company_quota=0.2)

        tt = [
            {"total": 0, "female": 0, "expected": True},
            {"total": 1, "female": 1, "expected": False},
            {"total": 2, "female": 1, "expected": True},
        ]

        for t in tt:
            counters = DrawCounters()
            counters.total = t["total"]
            counters.female = t["female"]

            assert must_pick_female(params, counters) == t["expected"]  # noqa: S101

    def test_must_not_pick_company(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=50, min_female_quota=0.35, max_company_quota=0.2)

        tt = [
            {"total": 0, "company": 0, "expected": True},
            {"total": 40, "company": 5, "expected": False},
        ]

        for t in tt:
            counters = DrawCounters()
            counters.total = t["total"]
            counters.company = t["company"]

            assert must_not_pick_company(params, counters) == t["expected"]  # noqa: S101

    def test_draw_all_females(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=10, min_female_quota=1, max_company_quota=0)

        for i in range(15):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 10  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            == 10  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.PASSED_TEST]).count()
            == 5  # noqa: PLR2004
        )  # noqa: S101

    def test_draw_all_females_not_enough(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=10, min_female_quota=1, max_company_quota=0)

        for i in range(9):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 10  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            == 9  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.male)
            .count()
            == 1
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.PASSED_TEST]).count()
            == 8  # noqa: PLR2004
        )  # noqa: S101

    def test_draw_1pc_females(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=6, min_female_quota=0.01, max_company_quota=0)

        for i in range(9):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 6  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            > 0
        )  # noqa: S101

    def test_draw_0_companies(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=8, min_female_quota=0, max_company_quota=0)

        for i in range(9):
            u = User.objects.create(email=f"company_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.company,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"student_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.student,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 8  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.company)
            .count()
            == 0
        )  # noqa: S101

    def test_draw_rejects_dont_count(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=10, min_female_quota=1, max_company_quota=0)

        for i in range(100):
            u = User.objects.create(email=f"rejected_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.REJECTED)

            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        to_draw_selections: list[Selection] = []
        for i in range(10):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            to_draw_selections.append(
                Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST),
            )

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 10  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            == 10  # noqa: PLR2004
        )  # noqa: S101
        for selection in to_draw_selections:
            selection.refresh_from_db()
            assert SelectionDomain.get_status(selection) == SelectionStatus.DRAWN  # noqa: S101

    def test_draw_dont_pick_scholarships(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=5, min_female_quota=0, max_company_quota=0)

        to_draw_selections: list[Selection] = []
        for i in range(3):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            to_draw_selections.append(
                Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST),
            )

        for i in range(2):
            u = User.objects.create(email=f"scholarship_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.scholarship,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 3  # noqa: PLR2004
        )  # noqa: S101
        for selection in to_draw_selections:
            selection.refresh_from_db()
            assert SelectionDomain.get_status(selection) == SelectionStatus.DRAWN  # noqa: S101

    def test_draw_pick_scholarships(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=5, min_female_quota=0, max_company_quota=0)

        to_draw_selections: list[Selection] = []
        for i in range(3):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            to_draw_selections.append(
                Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST),
            )

        for i in range(6):
            u = User.objects.create(email=f"scholarship_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.scholarship,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=True)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 5  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.scholarship)
            .count()
            == 5  # noqa: PLR2004
        )  # noqa: S101

    def test_draw_pick_scholarships_not_enough_females(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=5, min_female_quota=0.5, max_company_quota=0)

        to_draw_selections: list[Selection] = []
        for i in range(2):
            u = User.objects.create(email=f"scholarship_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.scholarship,
                gender=ProfileGenders.female,
            )
            to_draw_selections.append(
                Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST),
            )

        for i in range(5):
            u = User.objects.create(email=f"scholarship_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.scholarship,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=True)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 5  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.scholarship)
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            == 2  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.scholarship)
            .filter(user__profile__gender=ProfileGenders.male)
            .count()
            == 3  # noqa: PLR2004
        )  # noqa: S101

    def test_draw_pick_scholarships_not_enough(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=4, min_female_quota=0, max_company_quota=0)

        to_draw_selections: list[Selection] = []
        for i in range(2):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            to_draw_selections.append(
                Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST),
            )

        for i in range(2):
            u = User.objects.create(email=f"scholarship_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.scholarship,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=True)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 4  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.scholarship)
            .count()
            == 2  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .exclude(user__profile__ticket_type=ProfileTicketTypes.scholarship)
            .count()
            == 2  # noqa: PLR2004
        )  # noqa: S101

    def test_draw_none(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=8, min_female_quota=0, max_company_quota=0)

        for i in range(2):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"selected_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.SELECTED)

            u = User.objects.create(email=f"accpeted_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.ACCEPTED)

            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

            u = User.objects.create(email=f"selected_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.SELECTED)

            u = User.objects.create(email=f"accepted_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.ACCEPTED)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count() == 0
        )  # noqa: S101

    def test_draw_real(self) -> None:  # noqa: ANN101, D102
        params = DrawParams(number_of_seats=50, min_female_quota=0.35, max_company_quota=0.1)

        for i in range(100):
            u = User.objects.create(email=f"male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(30):
            u = User.objects.create(email=f"company_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.company,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(15):
            u = User.objects.create(email=f"student_male_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.student,
                gender=ProfileGenders.male,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(20):
            u = User.objects.create(email=f"female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.regular,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(5):
            u = User.objects.create(email=f"company_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.company,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        for i in range(7):
            u = User.objects.create(email=f"student_female_user_{i}@amd.com")
            Profile.objects.create(
                user=u,
                ticket_type=ProfileTicketTypes.student,
                gender=ProfileGenders.female,
            )
            Selection.objects.create(user=u, status=SelectionStatus.PASSED_TEST)

        draw(params, scholarships=False)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count()
            == 50  # noqa: PLR2004
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__gender=ProfileGenders.female)
            .count()
            > params.number_of_seats * params.min_female_quota
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN])
            .filter(user__profile__ticket_type=ProfileTicketTypes.company)
            .count()
            < params.number_of_seats * params.max_company_quota
        )  # noqa: S101

    def test_reject_draw(self) -> None:  # noqa: ANN101, D102
        u = User.objects.create(email="drawn_female_user@amd.com")
        Profile.objects.create(
            user=u,
            ticket_type=ProfileTicketTypes.company,
            gender=ProfileGenders.female,
        )
        selection = Selection.objects.create(user=u, status=SelectionStatus.DRAWN)

        reject_draw(selection)

        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.DRAWN]).count() == 0
        )  # noqa: S101
        assert (  # noqa: S101
            SelectionQueries.filter_by_status_in([SelectionStatus.PASSED_TEST]).count() == 1
        )  # noqa: S101

    def test_reject_draw_expection(self) -> None:  # noqa: ANN101, D102
        u = User.objects.create(email="selected_female_user@amd.com")
        Profile.objects.create(
            user=u,
            ticket_type=ProfileTicketTypes.company,
            gender=ProfileGenders.female,
        )
        selection = Selection.objects.create(user=u, status=SelectionStatus.SELECTED)

        with pytest.raises(DrawExceptionError):
            reject_draw(selection)
