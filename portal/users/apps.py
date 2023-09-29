import contextlib  # noqa: D100

from django.apps import AppConfig  # noqa: D100


class UsersAppConfig(AppConfig):  # noqa: D101
    name = "portal.users"
    verbose_name = "Users"

    def ready(self):  # noqa: ANN101, ANN201, D102
        with contextlib.suppress(ImportError):
            import users.signals  # noqa: F401
