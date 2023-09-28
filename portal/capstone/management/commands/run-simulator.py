from django.core.management.base import BaseCommand  # noqa: D100

from portal.capstone.simulator import run


class Command(BaseCommand):  # noqa: D101
    help = "Run simulators"

    def handle(self, *args, **options):  # noqa: D102
        run()
