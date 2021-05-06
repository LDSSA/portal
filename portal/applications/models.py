from logging import getLogger
from typing import NamedTuple

from django.db import models

logger = getLogger(__name__)


class SubmissionType(NamedTuple):
    uname: str
    max_score: int
    pass_score: int


class SubmissionTypes:
    coding_test = SubmissionType(
        uname="coding_test", max_score=20, pass_score=16
    )
    slu01 = SubmissionType(uname="slu01", max_score=20, pass_score=16)
    slu02 = SubmissionType(uname="slu02", max_score=20, pass_score=16)
    slu03 = SubmissionType(uname="slu03", max_score=20, pass_score=16)

    all = [coding_test, slu01, slu02, slu03]


class Submission(models.Model):
    application = models.ForeignKey(
        to="applications.Application",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    submission_type = models.CharField(null=False, max_length=20)

    file_location = models.TextField(null=False)

    score = models.IntegerField(default=0, null=False)
    feedback_location = models.TextField(null=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()


class SubmissionsException(Exception):
    detail = "submission error"


class SubmissionsClosedException(SubmissionsException):
    detail = "submission error (closed)"


class SubmissionsNotOpenException(SubmissionsException):
    detail = "submission error (not open yet)"


class Application(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # coding test ##########################################################
    coding_test_started_at = models.DateTimeField(null=True, default=None)

    # stores data about sent email
    # None -> email not sent
    # passed -> `you have passed` email sent
    # failed -> `you have failed` email sent
    application_over_email_sent = models.CharField(
        null=True, default=None, max_length=10, choices=[("passed", "failed")]
    )

    objects = models.Manager()
