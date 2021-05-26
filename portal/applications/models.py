from datetime import datetime, timezone
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


# TODO
class Challenge(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    file = models.FileField()
    max_score = models.FloatField(default=20)
    pass_score = models.FloatField(default=16)


def get_path(instance, filename):
    now_str = datetime.now(timezone.utc).strftime("%m_%d_%Y__%H_%M_%S")
    return f"{instance.submission_type}/{instance.application.user.username}/{filename}@{now_str}"


class Submission(models.Model):
    application = models.ForeignKey(
        to="applications.Application",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    submission_type = models.CharField(null=False, max_length=20)

    file = models.FileField(upload_to=get_path, null=True, blank=True)
    feedback = models.FileField(upload_to=get_path, null=True, blank=True)

    score = models.IntegerField(default=0, null=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


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
