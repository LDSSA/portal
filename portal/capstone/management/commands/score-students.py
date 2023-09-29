from django.core.management.base import BaseCommand  # noqa: D100, N999

from portal.capstone import models


class Command(BaseCommand):  # noqa: D101
    help = "Score capstone"  # noqa: A003

    def add_arguments(self, parser):  # noqa: ANN001, ANN101, ANN201, D102
        parser.add_argument("capstone")

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        capstone = models.Capstone.objects.get(name=options["capstone"])
        capstone.score()
