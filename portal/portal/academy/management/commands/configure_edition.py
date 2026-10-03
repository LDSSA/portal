"""Preview/apply the single active edition's calendar without deleting records."""

from django.core.management.base import BaseCommand

from portal.edition_management.calendar import SPECIALIZATIONS as SPECIALIZATIONS
from portal.edition_management.calendar import configure_batch10
from portal.edition_management.maintenance import configuration_guard


class Command(BaseCommand):
    help = "Preview the 2026/27 no-exam calendar. --apply changes configuration and existing curriculum dates only."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument(
            "--hackathon-2-date",
            default="2026-12-20",
            help="Hackathon 2 date; defaults to the confirmed 20 December 2026.",
        )

    @configuration_guard
    def handle(self, *args, **options):
        configure_batch10(options, self.stdout)
