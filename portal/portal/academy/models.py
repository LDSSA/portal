#from datetime import datetime

from django.conf import settings
from django.db import models

LISBON_TZ = timezone.utc


class Specialization(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class Unit(models.Model):
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.CASCADE,
        related_name="units",
    )

    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    due_date = models.DateField(default=timezone.now())
    open = models.BooleanField(default=False)

    checksum = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.specialization.code}/{self.code}"


def notebook_path(instance, filename):
    now = timezone.now().astimezone().isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/notebook_{now}.ipynb"


def feedback_path(instance, filename):
    now = timezone.now(LISBON_TZ).isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/feedback_{now}.ipynb"


class Grade(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="grades")
    created = models.DateTimeField(auto_now_add=True)
    notebook = models.FileField(upload_to=notebook_path, null=True, blank=True)

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
    score = models.FloatField(null=True, blank=True)
    message = models.TextField(blank=True)
    feedback = models.FileField(upload_to=feedback_path, null=True)
    on_time = models.BooleanField(default=True)
