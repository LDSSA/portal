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
    readonly_fields = ("admissions_mode", "registration_completed_at")
    fieldsets = (
        ("User", {"fields": ("name",)}),
        (
            "Status",
            {
                "fields": (
                    "admissions_mode",
                    "registration_completed_at",
                    "academy_type_preference",
                    "is_student",
                    "is_instructor",
                    "retain_account_on_next_edition_reset",
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
        "admissions_mode",
        "username",
        "is_student",
        "is_instructor",
        "retain_account_on_next_edition_reset",
        "name",
        "is_superuser",
        "can_graduate",
        "failed_or_dropped",
        "date_joined",
    ]
    search_fields = ["username", "name"]
    list_filter = (
        "admissions_mode",
        "is_student",
        "is_instructor",
        "is_staff",
        "is_superuser",
        "retain_account_on_next_edition_reset",
        "is_active",
        "groups",
        "can_graduate",
        "failed_or_dropped",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is None or not obj.can_choose_reset_retention:
            fields.append("retain_account_on_next_edition_reset")
        return fields
