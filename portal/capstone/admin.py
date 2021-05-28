from datetime import datetime, timezone

from django.contrib import admin

from portal.capstone import models


@admin.register(models.Capstone)
class CapstoneAdmin(admin.ModelAdmin):
    list_display = ("name",)
    fields = ("name", "scoring")


@admin.register(models.StudentApi)
class StudentApiAdmin(admin.ModelAdmin):
    list_display = ("capstone", "user", "url")
    fields = ("capstone", "user", "url")


@admin.register(models.Simulator)
class SimulatorAdmin(admin.ModelAdmin):
    list_display = ("name", "capstone", "status", "ends")
    fields = (
        "name",
        "capstone",
        "status",
        "path",
        "ends",
        "started",
        "interval",
    )
    readonly_fields = (
        "started",
        "interval",
    )


@admin.register(models.Datapoint)
class DatapointAdmin(admin.ModelAdmin):
    list_display = ("id", "simulator", "data")
    fields = ("simulator", "data", "outcome")
    list_filter = ("simulator",)


class OldFilter(admin.SimpleListFilter):
    title = "Old"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "old"

    def lookups(self, request, model_admin):
        return (("now", "now"),)

    def queryset(self, request, queryset):
        if self.value() == "now":
            return queryset.filter(due__lte=datetime.now(timezone.utc))


@admin.register(models.DueDatapoint)
class DueDatapointAdmin(admin.ModelAdmin):
    list_filter = (OldFilter, "state", "simulator", "user", "simulator")

    list_display = ("id", "simulator", "user", "datapoint", "state", "due")
    fields = (
        "simulator",
        "user",
        "datapoint",
        "state",
        "due",
        "url",
        "response_content",
        "response_exception",
        "response_traceback",
        "response_elapsed",
        "response_status",
        "response_timeout",
    )
    readonly_fields = (
        "simulator",
        "user",
        "datapoint",
        "due",
        "url",
        "response_content",
        "response_exception",
        "response_traceback",
        "response_elapsed",
        "response_status",
        "response_timeout",
    )
