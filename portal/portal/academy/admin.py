from django.contrib import admin
from django.db import transaction

from portal.academy import models
from portal.academy.forms import GradeAdminForm
from portal.academy.services import (
    refresh_certificate_eligibility,
    set_deadline_override,
)
from portal.users.models import User


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("code", "name")


@admin.register(models.Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "get_code",
        "name",
        "instructor",
        "due_date",
        "available_on",
        "required_for_certificate",
        "open",
    )
    fields = (
        "open",
        "due_date",
        "available_on",
        "required_for_certificate",
        "specialization",
        "code",
        "name",
        "description",
        "instructor",
        "checksum",
    )
    search_fields = ["instructor__username", "name", "code"]
    list_filter = ("specialization", "open", "required_for_certificate", "instructor")

    def get_code(self, obj):
        return str(obj)

    get_code.short_description = "Code"


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    form = GradeAdminForm
    list_display = (
        "unit",
        "user",
        "status",
        "created",
        "score",
        "on_time",
        "deadline_valid_override",
    )
    search_fields = [
        "unit__code",
        "user__username",
        "user__name",
    ]
    list_filter = (
        "user__is_student",
        "status",
        "unit",
        "user",
        "on_time",
        "deadline_valid_override",
    )
    fields = (
        "unit",
        "user",
        "status",
        "created",
        "score",
        "on_time",
        "deadline_valid_override",
        "deadline_override_reason",
        "deadline_override_by",
        "deadline_override_at",
        "notebook",
        "message",
    )
    readonly_fields = (
        "unit",
        "user",
        "created",
        "on_time",
        "deadline_override_by",
        "deadline_override_at",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            fields += ["deadline_valid_override", "deadline_override_reason"]
        return fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        User.objects.select_for_update().get(pk=obj.user_id)
        original = models.Grade.objects.select_for_update().get(pk=obj.pk)
        desired = form.cleaned_data.get(
            "deadline_valid_override", original.deadline_valid_override
        )
        reason = form.cleaned_data.get(
            "deadline_override_reason", original.deadline_override_reason
        )
        changed = (
            desired != original.deadline_valid_override
            or reason != original.deadline_override_reason
        )
        for field in (
            "created",
            "on_time",
            "deadline_valid_override",
            "deadline_override_reason",
            "deadline_override_by",
            "deadline_override_at",
        ):
            setattr(obj, field, getattr(original, field))
        super().save_model(request, obj, form, change)
        if changed:
            set_deadline_override(obj.pk, request.user, desired, reason)
            obj.refresh_from_db()
        refresh_certificate_eligibility(obj.user)


@admin.register(models.GradeDeadlineDecision)
class GradeDeadlineDecisionAdmin(admin.ModelAdmin):
    list_display = ("grade", "previous_value", "new_value", "actor_username", "created")
    search_fields = (
        "grade__user__username",
        "grade__unit__code",
        "reason",
        "actor_username",
    )
    readonly_fields = (
        "grade",
        "previous_value",
        "new_value",
        "reason",
        "actor",
        "actor_username",
        "created",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
