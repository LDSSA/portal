from http import HTTPStatus  # noqa: D100
from pathlib import Path

import pytest
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from requests import Response
from rest_framework.authtoken.models import Token

from portal.academy import models
from portal.users.models import User

PASSING_SCORE = 16


@pytest.fixture()
def auth_token(grader):  # noqa: ANN001, ANN201, D103
    token = Token.objects.create(user=grader)
    token.save()
    grader.save()
    return token.key


def setup_base_empty_grade_helper(user: User, unit: models.Unit) -> models.Grade:
    """Set up an empty grade before sending a request to the grading view."""
    grade = models.Grade(user=user, unit=unit)

    grade.status = "sent"
    grade.score = None
    grade.notebook = None
    grade.message = ""
    grade.save()

    return grade


def send_grader_request_helper(  # noqa: PLR0913
    base_url: str,
    token: str,
    grade: models.Grade,
    score: float,
    status: str = "graded",
    message: str = "",
    send_file: bool = True,  # noqa: FBT001, FBT002
) -> Response:
    """Set up an empty grade before sending a request to the grading view."""
    grade_update_dict = {"score": score, "status": status, "message": message, "notebook": None}

    if send_file:
        example_file = Path(Path(__file__).parent) / "example_notebook.ipynb"
        file_update_dict = {
            "notebook": SimpleUploadedFile(
                "example_notebook.ipynb",
                example_file.read_bytes(),
                "application/x-ipynb+json",
            ),
        }
    else:
        file_update_dict = {}
        grade_update_dict.update({"notebook": None, "status": "failed"})

    path_url = reverse("grading:academy-grade", kwargs={"pk": grade.pk}).lstrip("/")
    url = f"{base_url.rstrip('/')}/{path_url}"

    return requests.put(  # noqa: S113
        url,
        headers={"Authorization": f"Token {token}"},
        data=grade_update_dict,
        files=file_update_dict,
    )


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_grade_and_passed_specialization(  # noqa: ANN201, D103
    live_server,  # noqa: ANN001
    auth_token,  # noqa: ANN001
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    slu1,  # noqa: ANN001
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)

    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, PASSING_SCORE)

    assert response.status_code == HTTPStatus.OK, response.content  # noqa: S101

    grade_slu1.refresh_from_db()
    assert grade_slu1.score == PASSING_SCORE  # noqa: S101
    assert grade_slu1.status == "graded"  # noqa: S101
    assert grade_slu1.message == ""  # noqa: S101

    student.refresh_from_db()
    assert student.can_attend_next is True  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_grade_and_dont_pass_specialization(  # noqa: ANN201, D103, PLR0913
    live_server,  # noqa: ANN001
    auth_token,  # noqa: ANN001
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    slu1,  # noqa: ANN001
    slu2,  # noqa: ANN001, ARG001
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)

    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, PASSING_SCORE)

    assert response.status_code == HTTPStatus.OK, response.content  # noqa: S101

    grade_slu1.refresh_from_db()
    assert grade_slu1.score == PASSING_SCORE  # noqa: S101
    assert grade_slu1.status == "graded"  # noqa: S101
    assert grade_slu1.message == ""  # noqa: S101

    student.refresh_from_db()
    assert student.can_attend_next is False  # noqa: S101


@pytest.mark.django_db(transaction=True)
def test_academy_grading_view_set_slu1_and_slu2_grade_and_pass_specialization(  # noqa: ANN201, D103, PLR0913
    live_server,  # noqa: ANN001
    auth_token,  # noqa: ANN001
    db,  # noqa: ANN001, ARG001
    student,  # noqa: ANN001
    slu1,  # noqa: ANN001
    slu2,  # noqa: ANN001
):
    grade_slu1 = setup_base_empty_grade_helper(student, slu1)
    response = send_grader_request_helper(live_server.url, auth_token, grade_slu1, PASSING_SCORE)

    assert response.status_code == HTTPStatus.OK, response.content  # noqa: S101

    grade_slu2 = setup_base_empty_grade_helper(student, slu2)
    response = send_grader_request_helper(live_server.url, auth_token, grade_slu2, PASSING_SCORE)

    assert response.status_code == HTTPStatus.OK  # noqa: S101

    grade_slu2.refresh_from_db()
    assert grade_slu2.score == PASSING_SCORE  # noqa: S101
    assert grade_slu2.status == "graded"  # noqa: S101
    assert grade_slu2.message == ""  # noqa: S101

    student.refresh_from_db()
    assert student.can_attend_next is True  # noqa: S101
