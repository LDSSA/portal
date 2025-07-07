from datetime import datetime, timezone
from logging import getLogger

from django.conf import settings
from django.db import models

logger = getLogger(__name__)


LISBON_TZ = timezone.utc


class Challenge(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    file = models.FileField(blank=True)
    checksum = models.TextField(blank=True)
    max_score = models.FloatField(default=20)
    pass_score = models.FloatField(default=16)

    def __str__(self) -> str:
        return f"{self.code}"


def notebook_path(instance, filename):
    now = datetime.now(LISBON_TZ).isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/notebook_{now}.ipynb"


def feedback_path(instance, filename):
    now = datetime.now(LISBON_TZ).isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/feeback_{now}.ipynb"


class Submission(models.Model):
    application = models.ForeignKey(
        to="applications.Application",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unit = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    notebook = models.FileField(upload_to=notebook_path, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # From grading
    STATUSES = (
        ("never-submitted", "Unsubmitted"),
        ("sent", "Sent"),
        ("grading", "Grading"),
        ("failed", "Grading failed"),
        ("out-of-date", "Out-of-date"),
        ("checksum-failed", "Checksum verification failed"),
        ("graded", "Graded"),
    )
    status = models.CharField(
        max_length=1024, choices=STATUSES, default="never-submitted"
    )
    score = models.FloatField(default=0, null=False)
    message = models.TextField(blank=True)
    feedback = models.FileField(upload_to=feedback_path, null=True, blank=True)


class SubmissionsExceptionError(Exception):
    detail = "submission error"


class SubmissionsClosedExceptionError(SubmissionsExceptionError):
    detail = "submission error (closed)"


class SubmissionsNotOpenExceptionError(SubmissionsExceptionError):
    detail = "submission error (not open yet)"


class Application(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # coding test ##########################################################
    coding_test_started_at = models.DateTimeField(null=True, blank=True, default=None)
    coding_test_downloaded = models.IntegerField()
    #slu01_downloaded = models.IntegerField(default=0)
    #slu02_downloaded = models.IntegerField(default=0)
    #slu03_downloaded = models.IntegerField(default=0)

    # stores data about sent email
    # None -> email not sent
    # passed -> `you have passed` email sent
    # failed -> `you have failed` email sent
    application_over_email_sent = models.CharField(
        null=True,
        default=None,
        max_length=10,
        choices=[("passed", "Passed"), ("failed", "Failed")],
    )
