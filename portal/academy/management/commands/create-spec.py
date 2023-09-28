from django.core.management.base import BaseCommand, CommandError

from portal.academy.models import Specialization


class Command(BaseCommand):
    help = "Creates a specialization in portal"

    def add_arguments(self, parser):
        parser.add_argument("-c", "--code", type=str, required=True)
        parser.add_argument("-n", "--name", type=str, required=True)
        parser.add_argument("-d", "--description", type=str, default="")

    def handle(self, *args, **options):
        # TODO: revisit uniqueness of primary key
        spec = Specialization.objects.filter(code=options["code"]).first()
        if spec:
            self.stdout.write(self.style.SUCCESS("Specialization already existed: {}".format(spec)))
            return

        try:
            spec = Specialization(
                code=options.get("code"),
                name=options.get("name"),
                description=options.get("description"),
            )
            spec.save()
        except Exception as e:
            raise CommandError("Could not create specialization: {}".format(e))

        self.stdout.write(self.style.SUCCESS("Successfully created specialization {}".format(spec)))
