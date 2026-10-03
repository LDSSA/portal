from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from portal.edition_management.configuration import readiness_issues
from portal.edition_management.maintenance import schema_ready, state
from portal.edition_management.models import PortalState


class Command(BaseCommand):
    help = "Check migrations; --deployment-complete marks this release ready only after the deployment workflow verifies all pods."

    def add_arguments(self, parser):
        parser.add_argument("--deployment-complete", action="store_true")
        parser.add_argument("--calendar", action="store_true")
        parser.add_argument("--disable-reset", action="store_true")

    def handle(self, *args, **options):
        schema_ready()
        state()
        if options["disable_reset"]:
            PortalState.objects.filter(pk=1).update(ready_release="")
        if options["calendar"]:
            issues = readiness_issues()
            if issues:
                raise CommandError("; ".join(issues))
        if options["deployment_complete"]:
            PortalState.objects.filter(pk=1).update(
                ready_release=settings.EDITION_RELEASE
            )
        self.stdout.write("Migrations complete. No reset executed.")
