from datetime import datetime, timedelta, timezone

import pytest
from django.urls import reverse

from portal.academy.services import get_last_grade
from portal.academy.views import csvdata


@pytest.mark.django_db(transaction=True)
def test_student_unit_detail_view(client, db, student, slu1):
    client.login(username=student.username, password=student.password)
    url = reverse("academy:student-unit-detail", kwargs={"pk": slu1.pk})
    response = client.post(url, follow=True)

    # TODO: assert details on return

    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_instructor_unit_detail_view(client, db, instructor, slu1):
    client.login(username=instructor.username, password=instructor.password)
    url = reverse("academy:instructor-unit-detail", kwargs={"pk": slu1.pk})
    response = client.post(url, follow=True)

    # TODO: assert details on return

    assert response.status_code == 200


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
def test_grade_on_time(client, student, slu1):
    slu1.due_date = datetime.now(timezone.utc) + timedelta(days=5)
    slu1.save()

    client.force_login(student)
    client.post(reverse("academy:student-unit-detail", args=(slu1.pk,)))
    assert get_last_grade(slu1, student).on_time is True

    slu1.due_date = datetime.now(timezone.utc) - timedelta(days=5)
    slu1.save()

    client.post(reverse("academy:student-unit-detail", args=(slu1.pk,)))
    assert get_last_grade(slu1, student).on_time is False
