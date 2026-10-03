import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from portal.edition_management.executor import process
from portal.edition_management.jobs import refresh_jobs
from portal.edition_management.maintenance import (
    WORKER,
    MaintenanceBusy,
    lock,
    schema_ready,
)
from portal.edition_management.models import EditionRun, PortalState


class Command(BaseCommand):
    help = "Run the database-local edition/reset/backup worker. Never resets without an approved queued request."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        schema_ready()
        # A dedicated session owns the worker lock for its entire lifetime.
        with lock(WORKER, exclusive=True):
            with lock(exclusive=True), transaction.atomic():
                PortalState.objects.get_or_create(pk=1)
                current = PortalState.objects.select_for_update().get(pk=1)
                interrupted_resets = EditionRun.objects.filter(
                    kind="reset",
                    generation=current.generation,
                    status="running",
                )
                reset_was_interrupted = interrupted_resets.exists()
                EditionRun.objects.filter(status="running").update(
                    status="failed",
                    finished=timezone.now(),
                    error="Worker interrupted. A committed reset remains successful; an uncommitted reset rolled back and the previous edition resumed.",
                )
                another_reset_is_active = EditionRun.objects.filter(
                    kind="reset",
                    generation=current.generation,
                    status__in=("draft", "queued", "running"),
                ).exists()
                if (
                    reset_was_interrupted
                    and current.phase == "maintenance"
                    and not another_reset_is_active
                ):
                    current.phase = "open"
                    current.save(update_fields=["phase"])
            while True:
                PortalState.objects.filter(pk=1).update(
                    worker_seen=timezone.now(), worker_release=settings.EDITION_RELEASE
                )
                refresh_jobs()
                run = (
                    EditionRun.objects.filter(status="queued")
                    .order_by("created")
                    .first()
                )
                if run:
                    try:
                        process(run)
                    except MaintenanceBusy:
                        pass
                if options["once"]:
                    return
                # Do not close this connection: it owns the session-level worker lock.
                time.sleep(3)
