from django.core.management.base import BaseCommand

from portal.capstone import models
from portal.edition_management.maintenance import guarded


class Command(BaseCommand):
    help = "Score capstone"

    def add_arguments(self, parser):
        parser.add_argument("capstone")

    @guarded
    def handle(self, *args, **options):
        capstone = models.Capstone.objects.get(name=options["capstone"])
        capstone.score()
