from django.contrib import admin  # noqa: D100
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from portal.users.forms import UserCreationForm
from portal.users.models import UserWhitelist

User = get_user_model()


@admin.register(UserWhitelist)
class UserWhitelistAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ["username", "is_student", "is_instructor"]  # noqa: RUF012


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):  # noqa: D101
    add_form = UserCreationForm
    fieldsets = (
        ("User", {"fields": ("name",)}),
        (
            "Status",
            {
                "fields": (
                    "is_student",
                    "is_instructor",
                    "code_of_conduct_accepted",
                    "can_graduate",
                    "applying_for_scholarship",
                    "ticket_type",
                    "gender",
                    "profession",
                    "company",
                    "logo",
                    "github_username",
                    "slack_member_id",
                    "failed_or_dropped",
                ),
            },
        ),
        ("Keys", {"fields": ("deploy_private_key", "deploy_public_key")}),
        *auth_admin.UserAdmin.fieldsets,
    )
    list_display = [  # noqa: RUF012
        "username",
        "is_student",
        "is_instructor",
        "name",
        "is_superuser",
        "can_graduate",
        "failed_or_dropped",
    ]
    search_fields = ["username", "name"]  # noqa: RUF012
    list_filter = (
        "is_student",
        "is_instructor",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "can_graduate",
        "failed_or_dropped",
    )
