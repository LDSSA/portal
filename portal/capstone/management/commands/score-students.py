from django.core.management.base import BaseCommand

from portal.capstone import models


class Command(BaseCommand):
    help = "Score capstone"

    def add_arguments(self, parser):
        parser.add_argument("capstone")

    def handle(self, *args, **options):
        capstone = models.Capstone(name=options["capstone"])
        capstone.score()
