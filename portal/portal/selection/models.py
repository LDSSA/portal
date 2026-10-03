import uuid
from pathlib import Path

from django.db import models
from django.utils import timezone

from .status import SelectionStatus


class ScholarshipStatus(models.TextChoices):
    NOT_REQUESTED = "not_requested", "Not requested"
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Selection(models.Model):
    scholarship_status = models.CharField(
        max_length=20,
        choices=ScholarshipStatus.choices,
        default=ScholarshipStatus.NOT_REQUESTED,
    )
    scholarship_decided_at = models.DateTimeField(null=True, blank=True)
    scholarship_decided_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scholarship_decisions",
    )

    user = models.OneToOneField("users.User", on_delete=models.CASCADE, editable=False)

    status = models.CharField(
        default=SelectionStatus.PASSED_TEST, null=False, max_length=40
    )

    draw_rank = models.IntegerField(null=True, default=None)

    payment_value = models.FloatField(null=True, blank=True, default=None)
    ticket_type = models.CharField(null=True, blank=True, default=None, max_length=40)
    payment_due_date = models.DateTimeField(null=True, blank=True, default=None)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


doc_type_choices = [
    ("payment_proof", "Payment Proof"),
    ("student_id", "Student ID"),
]


def get_path(instance, filename):
    path = Path(filename)
    key_basename = path.parent / path.stem
    key_ext = path.suffix
    filename = f"{key_basename}_{uuid.uuid4().hex}{key_ext}"
    return f"payments/{instance.doc_type}/{instance.selection.user.username}/{filename}"


class SelectionDocument(models.Model):
    selection = models.ForeignKey(
        "selection.Selection",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc = models.FileField(upload_to=get_path, null=True, blank=True)
    doc_type = models.CharField(
        blank=False, null=False, max_length=20, choices=doc_type_choices
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SelectionLogs(models.Model):
    selection = models.ForeignKey(
        "selection.Selection",
        on_delete=models.CASCADE,
        related_name="logs",
        editable=False,
    )

    event = models.CharField(null=False, max_length=40, editable=False)
    message = models.TextField(null=False, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)


class EnrollmentEmail(models.Model):
    """Durable notifications committed with the enrollment change they describe."""

    selection = models.ForeignKey(
        Selection, on_delete=models.CASCADE, related_name="emails"
    )
    event_key = models.CharField(max_length=150, unique=True)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True)
