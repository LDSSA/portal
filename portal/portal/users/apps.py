from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    name = "portal.users"
    verbose_name = "Users"

    def ready(self):
        from . import signals  # noqa: F401
