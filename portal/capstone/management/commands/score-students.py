from django.core.management.base import BaseCommand  # noqa: D100

from portal.capstone import models


class Command(BaseCommand):  # noqa: D101
    help = "Score capstone"

    def add_arguments(self, parser):  # noqa: D102
        parser.add_argument("capstone")

    def handle(self, *args, **options):  # noqa: D102
        capstone = models.Capstone.objects.get(name=options["capstone"])
        capstone.score()
