import os  # noqa: D100
import uuid

from django.db import models

from .status import SelectionStatus


class Selection(models.Model):  # noqa: D101
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, editable=False)

    status = models.CharField(default=SelectionStatus.PASSED_TEST, null=False, max_length=40)

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


def get_path(instance, filename):  # noqa: D103
    key_basename, key_ext = os.path.splitext(filename)
    filename = f"{key_basename}_{uuid.uuid4().hex}{key_ext}"
    return f"payments/{instance.doc_type}/{instance.selection.user.username}/{filename}"


class SelectionDocument(models.Model):  # noqa: D101
    selection = models.ForeignKey(
        "selection.Selection",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc = models.FileField(upload_to=get_path, null=True, blank=True)
    doc_type = models.CharField(blank=False, null=False, max_length=20, choices=doc_type_choices)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SelectionLogs(models.Model):  # noqa: D101
    selection = models.ForeignKey(
        "selection.Selection",
        on_delete=models.CASCADE,
        related_name="logs",
        editable=False,
    )

    event = models.CharField(null=False, max_length=40, editable=False)
    message = models.TextField(null=False, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
