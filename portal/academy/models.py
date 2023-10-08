from datetime import datetime, timezone  # noqa: D100

from django.conf import settings
from django.db import models
from django.utils import timezone

LISBON_TZ = timezone.utc


class Specialization(models.Model):  # noqa: D101
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # noqa: ANN101, D105
        return self.code


class Unit(models.Model):  # noqa: D101
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.CASCADE,
        related_name="units",
    )

    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    due_date = models.DateField(default=timezone.now)
    open = models.BooleanField(default=False)  # noqa: A003

    checksum = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # noqa: ANN101, D105
        return f"{self.specialization.code}/{self.code}"


def notebook_path(instance, filename):  # noqa: ANN001, ANN201, ARG001, D103
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/notebook_{now}.ipynb"


def feedback_path(instance, filename):  # noqa: ANN001, ANN201, ARG001, D103
    now = datetime.now(LISBON_TZ).isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/feedback_{now}.ipynb"


class Grade(models.Model):  # noqa: D101, DJ008
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="grades")
    created = models.DateTimeField(auto_now_add=True)
    notebook = models.FileField(upload_to=notebook_path, null=True)

    STATUSES = (
        ("never-submitted", "Unsubmitted"),
        ("sent", "Sent"),
        ("grading", "Grading"),
        ("failed", "Grading failed"),
        ("out-of-date", "Out-of-date"),
        ("checksum-failed", "Checksum verification failed"),
        ("graded", "Graded"),
    )
    status = models.CharField(max_length=1024, choices=STATUSES, default="never-submitted")
    score = models.FloatField(null=True)
    message = models.TextField(blank=True)
    feedback = models.FileField(upload_to=feedback_path, null=True)
    on_time = models.BooleanField(default=True)
