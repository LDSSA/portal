# from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone

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
    due_date = models.DateField(default=timezone.localdate)
    required_for_certificate = models.BooleanField(default=True)
    open = models.BooleanField(default=False)
    available_on = models.DateField(null=True, blank=True)

    @property
    def submissions_open(self):
        from zoneinfo import ZoneInfo

        return self.open and (
            self.available_on is None
            or timezone.now().astimezone(ZoneInfo("Europe/Lisbon")).date()
            >= self.available_on
        )

    checksum = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.specialization.code}/{self.code}"


def notebook_path(instance, filename):
    now = timezone.now().astimezone().isoformat(timespec="seconds")
    return f"{instance.unit.code}/{instance.user.username}/notebook_{now}.ipynb"


def feedback_path(instance, filename):
    now = timezone.now().isoformat(timespec="seconds")
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
    deadline_valid_override = models.BooleanField(
        null=True,
        blank=True,
        help_text="Unknown uses the recorded on-time result; Yes accepts the deadline exception; No invalidates it.",
    )
    deadline_override_reason = models.TextField(blank=True)
    deadline_override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deadline_overrides",
    )
    deadline_override_at = models.DateTimeField(null=True, blank=True)

    @property
    def deadline_valid(self):
        return (
            self.on_time
            if self.deadline_valid_override is None
            else self.deadline_valid_override
        )


class GradeDeadlineDecision(models.Model):
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name="deadline_decisions"
    )
    previous_value = models.BooleanField(null=True)
    new_value = models.BooleanField(null=True)
    reason = models.TextField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    actor_username = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
