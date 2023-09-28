from django.core.management.base import BaseCommand, CommandError

from portal.capstone.simulator import run


class Command(BaseCommand):
    help = "Run simulators"

    def handle(self, *args, **options):
        run()
