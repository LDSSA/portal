import os
import pytest
import requests
from pathlib import Path
from requests import Response
from django.urls import reverse
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile

from portal.academy import models
from portal.users.models import User


@pytest.fixture
def auth_token(grader):
    token = Token.objects.create(user=grader)
    token.save()
    grader.save()
    return token.key


def setup_base_empty_grade_helper(user: User, unit: models.Unit) -> models.Grade:
    """
    Helper method to setup an empty grade before sending a request to the grading
    view.
    """
    grade = models.Grade(user=user, unit=unit)

    grade.status = "sent"
    grade.score = None
    grade.notebook = None
    grade.message = ""
    grade.save()

    return grade


def send_grader_request_helper(
    base_url: str,
    token: str,
    grade: models.Grade,
    score: float,
    status: str = "graded",
    message: str = "",
    send_file: bool = True
) -> Response:
    """
    Helper method to setup an empty grade before sending a request to the grading
    view.
    """
    grade_update_dict = {"score": score, "status": status, "message": message, "notebook": None}

    if send_file:
        example_file = Path(os.path.dirname(__file__)) / "example_notebook.ipynb"
        file_update_dict = {
                "notebook": SimpleUploadedFile(
                    "example_notebook.ipynb",
                    example_file.read_bytes(),
                    "application/x-ipynb+json"
                )
            }
    else:
        file_update_dict = {}
        grade_update_dict.update({"notebook": None, "status": "failed"})

    path_url = reverse('grading:academy-grade', kwargs={'pk': grade.pk}).lstrip('/')
    url = f"{base_url.rstrip('/')}/{path_url}"

    response = requests.put(
        url,
        headers={"Authorization": f"Token {token}"},
        data=grade_update_dict,
        files=file_update_dict,
    )
    return response


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_grade_and_passed_specialization(
    live_server,
    auth_token,
    db,
    student,
    slu1,
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)

    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, 16)

    assert response.status_code == 200, response.content

    grade_slu1.refresh_from_db()
    assert grade_slu1.score == 16
    assert grade_slu1.status == "graded"
    assert grade_slu1.message == ""

    student.refresh_from_db()
    assert student.can_attend_next is True


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_grade_and_dont_pass_specialization(
    live_server,
    auth_token,
    db,
    student,
    slu1,
    slu2,
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)

    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, 16)

    assert response.status_code == 200, response.content

    grade_slu1.refresh_from_db()
    assert grade_slu1.score == 16
    assert grade_slu1.status == "graded"
    assert grade_slu1.message == ""

    student.refresh_from_db()
    assert student.can_attend_next is False


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_and_slu2_grade_and_pass_specialization(
    live_server,
    auth_token,
    db,
    student,
    slu1,
    slu2,
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)
    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, 16)

    assert response.status_code == 200, response.content

    grade_slu2 = setup_base_empty_grade_helper(student, slu2)
    response = send_grader_request_helper(live_server.url, auth_token, grade_slu2, 16)

    assert response.status_code == 200

    grade_slu2.refresh_from_db()
    assert grade_slu2.score == 16
    assert grade_slu2.status == "graded"
    assert grade_slu2.message == ""

    student.refresh_from_db()
    assert student.can_attend_next is True
