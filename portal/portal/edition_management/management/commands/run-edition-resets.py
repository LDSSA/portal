import time

from django.conf import settings
from django.core.management.base import BaseCommand
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
            EditionRun.objects.filter(status="running").update(
                status="failed",
                finished=timezone.now(),
                error="Worker interrupted. A committed reset remains successful; an uncommitted reset rolled back. Review maintenance state and prepare a new preview.",
            )
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
