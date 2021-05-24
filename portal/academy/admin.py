from django.contrib import admin
from portal.academy import models


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
        "open",
    )
    fields = (
        "open",
        "due_date",
        "specialization",
        "code",
        "name",
        "description",
        "instructor",
        "checksum",
    )
    search_fields = ["instructor__username", "name", "unit__code"]
    list_filter = ("specialization", "open", "instructor")

    def get_code(self, obj):
        return str(obj)

    get_code.short_description = "Code"


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "unit",
        "student",
        "status",
        "created",
        "score",
    )
    search_fields = [
        "unit__code",
        "student__username",
        "student__name",
    ]
    list_filter = (
        "student__is_student",
        "status",
        "unit",
        "student",
    )
    fields = (
        "unit",
        "student",
        "status",
        "created",
        "score",
        "notebook",
        "message",
    )
    readonly_fields = ("created",)
