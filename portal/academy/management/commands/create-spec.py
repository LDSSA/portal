from django.core.management.base import BaseCommand, CommandError  # noqa: D100, N999

from portal.academy.models import Specialization


class Command(BaseCommand):  # noqa: D101
    help = "Creates a specialization in portal"  # noqa: A003

    def add_arguments(self, parser):  # noqa: ANN001, ANN101, ANN201, D102
        parser.add_argument("-c", "--code", type=str, required=True)
        parser.add_argument("-n", "--name", type=str, required=True)
        parser.add_argument("-d", "--description", type=str, default="")

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        # TODO: revisit uniqueness of primary key  # noqa: FIX002, TD002, TD003
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
        except Exception as e:  # noqa: BLE001
            msg = f"Could not create specialization: {e}"
            raise CommandError(msg) from e

        self.stdout.write(self.style.SUCCESS("Successfully created specialization {}".format(spec)))
