import uuid

from django.conf import settings
from django.db import models


class PortalState(models.Model):
    """One database-local gate. Never included in edition deletion."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    phase = models.CharField(max_length=20, default="open")
    generation = models.PositiveIntegerField(default=0)
    ready_release = models.CharField(max_length=100, blank=True)
    worker_seen = models.DateTimeField(null=True)
    worker_release = models.CharField(max_length=100, blank=True)


class EditionRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=12, default="reset")
    status = models.CharField(max_length=20, default="draft")
    generation = models.PositiveIntegerField(default=0)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    actor_username = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True)
    release = models.CharField(max_length=100)
    database = models.CharField(max_length=255)
    plan = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=64, blank=True)
    backup_first = models.BooleanField(default=True)
    backup_name = models.CharField(max_length=255, blank=True)
    backup_sha256 = models.CharField(max_length=64, blank=True)
    backup_bytes = models.BigIntegerField(default=0)
    backup_deleted = models.BooleanField(default=False)
    result = models.JSONField(default=dict)
    error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Edition reset"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.kind}: {self.status} ({self.created})"


class GradingJob(models.Model):
    """External jobs must finish before resetting shared database/file references."""

    name = models.CharField(max_length=100, primary_key=True)
    backend = models.CharField(max_length=12)
    remote_seen = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="launching")
    created = models.DateTimeField(auto_now_add=True)
