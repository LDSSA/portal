from django.core.management.base import BaseCommand  # noqa: D100, N999

from portal.capstone.simulator import run


class Command(BaseCommand):  # noqa: D101
    help = "Run simulators"  # noqa: A003

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        run()
