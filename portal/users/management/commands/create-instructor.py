from django.core.management.base import BaseCommand, CommandError
from portal.users.management.commands._create_user import create_user, add_user_options


class Command(BaseCommand):
    help = 'Creates an instructor user in portal'

    def add_arguments(self, parser):
        add_user_options(parser)

    def handle(self, *args, **options):
        try:
            user = create_user(user_type="instructor", **options)
        except Exception as e:
            raise CommandError("Could not create instructor: {}".format(e))

        self.stdout.write(self.style.SUCCESS("Successfully created instructor {}".format(user)))
