import pytest
from django.urls import reverse


@pytest.mark.django_db(transaction=True)
def test_student_unit_detail_view(client, db, student, slu1):
    client.login(username=student.username, password=student.password)
    url = reverse('academy:student-unit-detail', kwargs={'pk': slu1.pk})
    response = client.post(url, follow=True)

    # TODO: assert details on return

    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_instructor_unit_detail_view(client, db, instructor, slu1):
    client.login(username=instructor.username, password=instructor.password)
    url = reverse('academy:instructor-unit-detail', kwargs={'pk': slu1.pk})
    response = client.post(url, follow=True)

    # TODO: assert details on return

    assert response.status_code == 200
