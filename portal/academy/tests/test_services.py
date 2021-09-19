import pytest

from portal.hackathons.models import Attendance
from portal.academy.services import check_graduation_status


@pytest.fixture
def attendances_graduate_ok(student, hackathon1, hackathon2, hackathon3):
    """
    Set student attendances for case when no hacakhon was missed
    """

    attendances = []
    for hack in [hackathon1, hackathon2, hackathon3]:
        attendance = Attendance.objects.create(
            hackathon=hack,
            user=student,
            present=True,
        )
        attendances.append(attendance)
    return attendances


@pytest.fixture
def attendances_graduate_ok_one_missed(student, hackathon1, hackathon2, hackathon3):
    """
    Set student attendances for case when only one non-mandatory hackathon was missed
    """

    attendances = []

    # Set first hackathon as missed
    attendance = Attendance.objects.create(
        hackathon=hackathon2,
        user=student,
        present=False,
    )
    attendances.append(attendance)

    for hack in [hackathon1, hackathon3]:
        attendance = Attendance.objects.create(
            hackathon=hack,
            user=student,
            present=True,
        )
        attendances.append(attendance)
    return attendances


@pytest.fixture
def attendances_graduation_fail_first_missed(student, hackathon1, hackathon2, hackathon3):
    """
    Set student attendances for case when first hackathon was missed
    """

    attendances = []

    # Set first hackathon as missed
    attendance = Attendance.objects.create(
        hackathon=hackathon1,
        user=student,
        present=False,
    )
    attendances.append(attendance)

    for hack in [hackathon2, hackathon3]:
        attendance = Attendance.objects.create(
            hackathon=hack,
            user=student,
            present=True,
        )
        attendances.append(attendance)
    return attendances


@pytest.fixture
def attendances_graduation_fail_too_many_missed(student, hackathon1, hackathon2, hackathon3):
    """
    Set student attendances for case when too many hackathons were missed, even
    if the first one was attended
    """

    attendances = []

    # Set first hackathon as missed
    attendance = Attendance.objects.create(
        hackathon=hackathon1,
        user=student,
        present=True,
    )
    attendances.append(attendance)

    for hack in [hackathon2, hackathon3]:
        attendance = Attendance.objects.create(
            hackathon=hack,
            user=student,
            present=False,
        )
        attendances.append(attendance)
    return attendances


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_ok(
    db,
    student,
    attendances_graduate_ok
):
    """
    Checks student can graduate when all conditions are met:

    - student has attended first hackathon
    - student has missed at most only 1 hackathon

    Test case when student has attended all hackathons
    """
    assert check_graduation_status(student) is True


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_ok_missed_one_not_first(
    db,
    student,
    attendances_graduate_ok_one_missed
):
    """
    Checks student can graduate when all conditions are met:

    - student has attended first hackathon
    - student has missed at most only 1 hackathon

    Test case when student has missed only 1 hackathon (not first)
    """
    assert check_graduation_status(student) is True


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_fail_missed_first(
    db,
    student,
    attendances_graduation_fail_first_missed
):
    """
    Checks student can not graduate when one of the following conditions are met:

    - student has missed first hackathon
    - student has missed at more than 1 hackathon

    Test case when student has missed first hackathon
    """

    assert check_graduation_status(student) is False


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_fail_missed_too_many(
    db,
    student,
    attendances_graduation_fail_too_many_missed
):
    """
    Checks student can not graduate when one of the following conditions are met:

    - student has missed first hackathon
    - student has missed at more than 1 hackathon

    Test case when student has missed more than one hackathon (even if not first)
    """

    assert check_graduation_status(student) is False
