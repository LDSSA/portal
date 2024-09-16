from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from portal.users.forms import UserCreationForm
from portal.users.models import UserWhitelist

User = get_user_model()


@admin.register(UserWhitelist)
class UserWhitelistAdmin(admin.ModelAdmin):
    list_display = ["username", "is_student", "is_instructor"]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
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
                    "github_username",
                    "slack_member_id",
                    "failed_or_dropped",
                ),
            },
        ),
        ("Keys", {"fields": ("deploy_private_key", "deploy_public_key")}),
        *auth_admin.UserAdmin.fieldsets,
    )
    list_display = [
        "username",
        "is_student",
        "is_instructor",
        "name",
        "is_superuser",
        "can_graduate",
        "failed_or_dropped",
        "date_joined",
    ]
    search_fields = ["username", "name"]
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
