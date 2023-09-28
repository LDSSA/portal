from django.core.management.base import BaseCommand, CommandError

from portal.users.management.commands._create_user import add_user_options, create_user


class Command(BaseCommand):
    help = "Creates an instructor user in portal"

    def add_arguments(self, parser):
        add_user_options(parser)

    def handle(self, *args, **options):
        try:
            user = create_user(user_type="instructor", **options)
        except Exception as e:
            raise CommandError(f"Could not create instructor: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully created instructor {user}"))
