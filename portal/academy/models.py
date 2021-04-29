import random
import string

from django.db import models
from django.conf import settings
from django.utils import timezone


class Specialization(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class Unit(models.Model):
    specialization = models.ForeignKey(
        Specialization, on_delete=models.CASCADE, related_name="units"
    )

    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    due_date = models.DateField(default=timezone.now)
    open = models.BooleanField(default=False)

    checksum = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.specialization.code}/{self.code}"


def notebook_path(instance, filename):
    date = str(timezone.now()).split(" ")[0]
    randstr = "".join(random.choices(string.ascii_lowercase, k=8))
    return (
        f"{instance.student.username}_{instance.unit.code}"
        f"_{date}_{randstr}.ipynb"
    )


class Grade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="grades"
    )
    score = models.FloatField(null=True)
    notebook = models.FileField(upload_to=notebook_path, null=True)

    STATUSES = (
        ("never-submitted", "Unsubmitted"),
        ("sent", "Sent"),
        ("grading", "Grading"),
        ("failed", "Grading failed"),
        ("out-of-date", "Out-of-date"),
        ("graded", "Graded"),
    )
    status = models.CharField(
        max_length=1024, choices=STATUSES, default="never-submitted"
    )
    message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
