from django.core.management.base import BaseCommand, CommandError  # noqa: D100

from portal.academy.models import Specialization


class Command(BaseCommand):  # noqa: D101
    help = "Creates a specialization in portal"

    def add_arguments(self, parser):  # noqa: D102
        parser.add_argument("-c", "--code", type=str, required=True)
        parser.add_argument("-n", "--name", type=str, required=True)
        parser.add_argument("-d", "--description", type=str, default="")

    def handle(self, *args, **options):  # noqa: D102
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
            raise CommandError(f"Could not create specialization: {e}")

        self.stdout.write(self.style.SUCCESS("Successfully created specialization {}".format(spec)))
