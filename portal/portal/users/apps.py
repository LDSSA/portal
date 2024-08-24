import contextlib

from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    name = "portal.users"
    verbose_name = "Users"

    def ready(self):
        with contextlib.suppress(ImportError):
            pass
