from django.apps import AppConfig  # noqa: D100


class UsersAppConfig(AppConfig):  # noqa: D101
    name = "portal.users"
    verbose_name = "Users"

    def ready(self):  # noqa: D102
        try:
            import users.signals  # noqa F401
        except ImportError:
            pass
