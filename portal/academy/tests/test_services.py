from datetime import datetime  # noqa: D100

import pytest
from dateutil import tz

from portal.academy.models import Grade
from portal.academy.services import (
    check_complete_specialization,
    check_graduation_status,
    csvdata,
    get_best_grade,
    get_last_grade,
)
from portal.hackathons.models import Attendance

PASSING_SCORE = 16
MAX_SCORE = 20
LISBON_TZ = tz.gettz("Europe/Lisbon")


@pytest.fixture()
def grade_slu1_failed(student, slu1):  # noqa: ANN001, ANN201, D103
    return Grade.objects.create(
        user=student,
        unit=slu1,
        created=datetime(year=2021, month=8, day=15, tzinfo=LISBON_TZ),
        status="graded",
        score=1,
        message="",
    )


@pytest.fixture()
def grade_slu2_failed(student, slu2):  # noqa: ANN001, ANN201, D103
    return Grade.objects.create(
        user=student,
        unit=slu2,
        created=datetime(year=2021, month=8, day=15, tzinfo=LISBON_TZ),
        status="graded",
        score=14,
        message="",
    )


@pytest.fixture()
def attendances_graduate_ok(student, hackathon1, hackathon2, hackathon3):  # noqa: ANN001, ANN201
    """Set student attendances for case when no hacakhon was missed."""
    attendances = []
    for hack in [hackathon1, hackathon2, hackathon3]:
        attendance = Attendance.objects.create(
            hackathon=hack,
            user=student,
            present=True,
        )
        attendances.append(attendance)
    return attendances


@pytest.fixture()
def attendances_graduate_ok_one_missed(  # noqa: ANN201
    student, hackathon1, hackathon2, hackathon3  # noqa: ANN001
):  # noqa: ANN001, ANN201
    """Set student attendances for case when only one non-mandatory hackathon was missed."""
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


@pytest.fixture()
def attendances_graduation_fail_first_missed(  # noqa: ANN201
    student, hackathon1, hackathon2, hackathon3  # noqa: ANN001
):  # noqa: ANN001, ANN201
    """Set student attendances for case when first hackathon was missed."""
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


@pytest.fixture()
def attendances_graduation_fail_too_many_missed(  # noqa: ANN201
    student, hackathon1, hackathon2, hackathon3  # noqa: ANN001
):  # noqa: ANN001, ANN201
    """Set student attendances.

    Case when too many hackathons were missed, even if the first one was attended
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
def test_check_graduation_status_ok(  # noqa: ANN201
    # db,  # noqa: ERA001
    student,  # noqa: ANN001
    # attendances_graduate_ok # noqa: ERA001
):  # noqa:ANN201, ARG001
    """Checks the student can graduate when all conditions are met.

    - student has attended first hackathon
    - student has missed at most only 1 hackathon

    Test case when student has attended all hackathons
    """
    assert check_graduation_status(student) is True  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_ok_missed_one_not_first(  # noqa: ANN201
    # db,  # noqa: ERA001
    student,  # noqa: ANN001
    # attendances_graduate_ok_one_missed,  # noqa: ERA001
):
    """Checks student can graduate when all conditions are met.

    - student has attended first hackathon
    - student has missed at most only 1 hackathon

    Test case when student has missed only 1 hackathon (not first)
    """
    assert check_graduation_status(student) is True  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_fail_missed_first(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    attendances_graduation_fail_first_missed,  # noqa: ANN001, ARG001
):
    """Checks student can not graduate when one of the following conditions are met.

    - student has missed first hackathon
    - student has missed at more than 1 hackathon

    Test case when student has missed first hackathon
    """
    assert check_graduation_status(student) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_graduation_status_fail_missed_too_many(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    attendances_graduation_fail_too_many_missed,  # noqa: ANN001, ARG001
):
    """Checks student can not graduate when one of the following conditions are met.

    - student has missed first hackathon
    - student has missed at more than 1 hackathon

    Test case when student has missed more than one hackathon (even if not first)
    """
    assert check_graduation_status(student) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_ok(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    grade_slu1,  # noqa: ANN001, ARG001
    grade_slu2,  # noqa: ANN001, ARG001
):
    """Checks student completed specialization when both grades exist and are above 16."""
    assert check_complete_specialization(student, specialization) is True  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_failed_slu1(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    grade_slu1_failed,  # noqa: ANN001, ARG001
    grade_slu2,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs was failed."""
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_failed_slu2(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    grade_slu1,  # noqa: ANN001, ARG001
    grade_slu2_failed,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs was failed."""
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu1(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    slu1,  # noqa: ANN001, ARG001
    grade_slu2,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs is missing."""
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu2(  # noqa: ANN201
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    grade_slu1,  # noqa: ANN001, ARG001
    slu2,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs is missing."""
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu1_but_two_attempts_slu2(  # noqa: ANN201, PLR0913
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    slu1,  # noqa: ANN001, ARG001
    grade_slu2,  # noqa: ANN001, ARG001
    grade_slu2_failed,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs is missing.

    This test also checks that even when there are repeated grades on other units
    the verification doesn't consider them
    """
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_slu2_but_two_attempts_slu1(  # noqa: ANN201, PLR0913
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    grade_slu1,  # noqa: ANN001, ARG001
    grade_slu1_failed,  # noqa: ANN001, ARG001
    slu2,  # noqa: ANN001, ARG001
):
    """Checks student did not completed specialization when one of the SLUs is missing.

    This test also checks that even when there are repeated grades on other units
    the verification doesn't consider them
    """
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_check_complete_specialization_missing_all(  # noqa: ANN201
    # db,  # noqa: ERA001
    student,  # noqa: ANN001
    specialization,  # noqa: ANN001
    slu1,  # noqa: ANN001, ARG001
    slu2,  # noqa: ANN001, ARG001
):
    """Checks completion check returns False when no grade is available."""
    assert check_complete_specialization(student, specialization) is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_csvdata(  # noqa: ANN201, PLR0913
    # db,  # noqa: ERA001
    specialization,  # noqa: ANN001
    slu1,  # noqa: ANN001
    slu2,  # noqa: ANN001
    student,  # noqa: ANN001
    grade_slu1,  # noqa: ANN001
    grade_slu2,  # noqa: ANN001
):  # noqa: ARG001, PLR0913
    """Test creation of csv file from table of student/unit grades."""
    specialization.unit_count = 2
    spc_list = [specialization]
    unit_list = [slu1, slu2]
    object_list = [
        {
            "user": student,
            "grades": [grade_slu1, grade_slu2],
            "submission_date": datetime(year=2021, month=8, day=15, tzinfo=LISBON_TZ),
            "total_score": 38,
        },
    ]
    text = csvdata(spc_list, unit_list, object_list)
    assert (  # noqa: S101
        text == "username,slack_id,submission_date,total_score,S01-SLU01,S01-SLU02\r\n"
        "test_student,U12J14XV12Z,2021-08-15 00:00:00,38,18,20\r\n"
    )


@pytest.mark.django_db(transaction=True)
def test_grade_retrieve(slu1, student, student2):  # noqa: ANN001, ANN201
    """Ensure grades are correctly retrieved."""
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
    Grade.objects.create(user=student, unit=slu1, status="graded", score=20, on_time=False)

    assert get_last_grade(slu1, student).score == MAX_SCORE  # noqa: S101
    assert get_best_grade(slu1, student).score == PASSING_SCORE  # noqa: S101

    assert get_last_grade(slu1, student2).score is None  # noqa: S101
    assert get_best_grade(slu1, student2).score is None  # noqa: S101
