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
def auth_token(grader):
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


def send_grader_request_helper(
    base_url: str,
    token: str,
    grade: models.Grade,
    score: float,
    status: str = "graded",
    message: str = "",
    send_file: bool = True,
) -> Response:
    """Set up an empty grade before sending a request to the grading view."""
    grade_update_dict = {
        "score": score,
        "status": status,
        "message": message,
        "notebook": None,
    }

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

    return requests.put(
        url,
        headers={"Authorization": f"Token {token}"},
        data=grade_update_dict,
        files=file_update_dict,
    )
