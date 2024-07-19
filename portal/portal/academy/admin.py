from django.contrib import admin  # noqa: D100

from portal.academy import models


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ("code", "name")


@admin.register(models.Unit)
class UnitAdmin(admin.ModelAdmin):  # noqa: D101
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
    search_fields = ["instructor__username", "name", "unit__code"]  # noqa: RUF012
    list_filter = ("specialization", "open", "instructor")

    def get_code(self, obj):  # noqa: ANN001, ANN101, ANN201, D102
        return str(obj)

    get_code.short_description = "Code"


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = (
        "unit",
        "user",
        "status",
        "created",
        "score",
        "on_time",
    )
    search_fields = [  # noqa: RUF012
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
    )
    fields = (
        "unit",
        "user",
        "status",
        "created",
        "score",
        "on_time",
        "notebook",
        "message",
    )
    readonly_fields = ("created",)
