import uuid

import dateutil.parser
from django.core.management.base import BaseCommand, CommandError

from portal.academy.models import Specialization, Unit
from portal.users.models import User


class Command(BaseCommand):
    help = "Creates a unit in portal"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--specialization", type=str, required=True)
        parser.add_argument("-c", "--code", type=str, required=True)
        parser.add_argument("-n", "--name", type=str, required=True)
        parser.add_argument("-d", "--description", type=str, default="")
        parser.add_argument("-i", "--instructor", type=str, default=None)
        parser.add_argument(
            "-due", "--duedate", type=str, help="Due date (eg. '2020-04-10')"
        )
        parser.add_argument(
            "-cs",
            "--checksum",
            type=str,
            default=None,
            help="Checksum (will be random if empty)",
        )
        parser.add_argument("--open", action="store_true")

    def handle(self, *args, **options):
        # TODO: revisit uniqueness of primary key
        unit = Unit.objects.filter(code=options["code"]).first()
        if unit:
            self.stdout.write(self.style.SUCCESS(f"Unit already existed: {unit}"))
            return

        instructor_opt = options.get("instructor")
        try:
            specialization = Specialization.objects.get(code=options["specialization"])
            if instructor_opt:
                instructor = User.objects.get(username=instructor_opt)
            else:
                instructor = User.objects.first()
        except Exception as e:
            msg = f"Could not create unit: dependency not met ({e})"
            raise CommandError(msg) from e

        checksum = options.get("checksum")
        if not checksum:
            checksum = uuid.uuid4()
        try:
            unit = Unit(
                specialization=specialization,
                code=options["code"],
                name=options["name"],
                description=options["description"],
                instructor=instructor,
                due_date=dateutil.parser.parse(options["duedate"]),
                open=options["open"],
                checksum=checksum,
            )
            unit.save()

        except Exception as e:
            msg = f"Could not create unit: {e}"
            raise CommandError(msg) from e

        self.stdout.write(self.style.SUCCESS(f"Successfully created unit {unit}"))
