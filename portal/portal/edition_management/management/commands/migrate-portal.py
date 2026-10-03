import time

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from portal.edition_management.maintenance import MaintenanceBusy, lock, state


class Command(BaseCommand):
    help = "Serialize deployment migrations on the connected database; never reset edition data."

    def handle(self, *args, **options):
        deadline = time.monotonic() + 120
        while True:
            try:
                return self.migrate()
            except MaintenanceBusy as exc:
                if time.monotonic() >= deadline:
                    raise CommandError(
                        "Timed out waiting for active portal operations."
                    ) from exc
                time.sleep(1)

    def migrate(self):
        with lock(exclusive=True):
            tables = connection.introspection.table_names()
            if "edition_management_editionrun" in tables:
                from portal.edition_management.models import EditionRun

                if (
                    EditionRun.objects.filter(status__in=("queued", "running")).exists()
                    or state().phase == "maintenance"
                ):
                    raise CommandError(
                        "Finish/cancel edition maintenance before deploying."
                    )
            call_command("migrate", interactive=False)
            current = state()
            current.ready_release = ""
            current.save(update_fields=["ready_release"])
