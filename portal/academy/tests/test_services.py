import pytest
from datetime import datetime

from portal.academy.models import Grade
from portal.academy.services import (
    check_graduation_status,
    check_complete_specialization,
    csvdata,
)
from portal.academy.services import get_last_grade, get_best_grade
from portal.hackathons.models import Attendance


@pytest.fixture
def grade_slu1_failed(student, slu1):
    grade = Grade.objects.create(
        user=student,
        unit=slu1,
        created=datetime(year=2021, month=8, day=15),
        status="graded",
        score=1,
        message="",
    )
    return grade


@pytest.fixture
def grade_slu2_failed(student, slu2):
    grade = Grade.objects.create(
        user=student,
        unit=slu2,
        created=datetime(year=2021, month=8, day=15),
        status="graded",
        score=14,
        message="",
    )
    return grade


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
def attendances_graduation_fail_first_missed(
    student, hackathon1, hackathon2, hackathon3
):
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
def attendances_graduation_fail_too_many_missed(
    student, hackathon1, hackathon2, hackathon3
):
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
def test_check_graduation_status_ok(db, student, attendances_graduate_ok):
    """
    Checks student can graduate when all conditions are met:

    - student has attended first hackathon
    - student has missed at most only 1 hackathon

    Test case when student has attended all hackathons
    """
    assert check_graduation_status(student) is True


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_ok_missed_one_not_first(
    db, student, attendances_graduate_ok_one_missed
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
    db, student, attendances_graduation_fail_first_missed
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
    db, student, attendances_graduation_fail_too_many_missed
):
    """
    Checks student can not graduate when one of the following conditions are met:

    - student has missed first hackathon
    - student has missed at more than 1 hackathon

    Test case when student has missed more than one hackathon (even if not first)
    """

    assert check_graduation_status(student) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_ok(
    db,
    student,
    specialization,
    grade_slu1,
    grade_slu2,
):
    """
    Checks student completed specialization when both grades exist and are above 16
    """

    assert check_complete_specialization(student, specialization) is True


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_failed_slu1(
    db,
    student,
    specialization,
    grade_slu1_failed,
    grade_slu2,
):
    """
    Checks student did not completed specialization when one of the SLUs was failed
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_failed_slu2(
    db,
    student,
    specialization,
    grade_slu1,
    grade_slu2_failed,
):
    """
    Checks student did not completed specialization when one of the SLUs was failed
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu1(
    db,
    student,
    specialization,
    slu1,
    grade_slu2,
):
    """
    Checks student did not completed specialization when one of the SLUs is missing
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu2(
    db,
    student,
    specialization,
    grade_slu1,
    slu2,
):
    """
    Checks student did not completed specialization when one of the SLUs is missing
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu1_but_two_attempts_slu2(
    db, student, specialization, slu1, grade_slu2, grade_slu2_failed
):
    """
    Checks student did not completed specialization when one of the SLUs is missing.

    This test also checks that even when there are repeated grades on other units
    the verification doesn't consider them
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu2_but_two_attempts_slu1(
    db,
    student,
    specialization,
    grade_slu1,
    grade_slu1_failed,
    slu2,
):
    """
    Checks student did not completed specialization when one of the SLUs is missing

    This test also checks that even when there are repeated grades on other units
    the verification doesn't consider them
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_all(
    db,
    student,
    specialization,
    slu1,
    slu2,
):
    """
    Checks completion check returns False when no grade is available
    """

    assert check_complete_specialization(student, specialization) is False


@pytest.mark.django_db(transaction=True)
def test_csvdata(db, specialization, slu1, slu2, student, grade_slu1, grade_slu2):
    """
    Test creation of csv file from table of student/unit grades
    """

    specialization.unit_count = 2
    spc_list = [specialization]
    unit_list = [slu1, slu2]
    object_list = [
        {
            "user": student,
            "grades": [grade_slu1, grade_slu2],
            "submission_date": datetime(year=2021, month=8, day=15),
            "total_score": 38,
        }
    ]
    text = csvdata(spc_list, unit_list, object_list)
    assert (
        text == "username,slack_id,submission_date,total_score,S01-SLU01,S01-SLU02\r\n"
        "test_student,U12J14XV12Z,2021-08-15 00:00:00,38,18,20\r\n"
    )


@pytest.mark.django_db(transaction=True)
def test_grade_retrieve(slu1, student, student2):
    """
    Ensure grades are correctly retrieved.
    """
    Grade.objects.create(
        user=student,
        unit=slu1,
        status="graded",
        score=16,
    )
    Grade.objects.create(
        user=student,
        unit=slu1,
        status="graded",
        score=14,
    )
    Grade.objects.create(
        user=student, unit=slu1, status="graded", score=20, on_time=False
    )

    assert get_last_grade(slu1, student).score == 20
    assert get_best_grade(slu1, student).score == 16

    assert get_last_grade(slu1, student2).score == None
    assert get_best_grade(slu1, student2).score == None
