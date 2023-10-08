from django.core.management.base import BaseCommand, CommandError  # noqa: D100, N999

from portal.users.management.commands._create_user import add_user_options, create_user


class Command(BaseCommand):  # noqa: D101
    help = "Creates an instructor user in portal"  # noqa: A003

    def add_arguments(self, parser):  # noqa: ANN001, ANN101, ANN201, D102
        add_user_options(parser)

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        try:
            user = create_user(user_type="instructor", **options)
        except Exception as e:  # noqa: BLE001
            msg = f"Could not create instructor: {e}"
            raise CommandError(msg) from e

        self.stdout.write(self.style.SUCCESS(f"Successfully created instructor {user}"))
