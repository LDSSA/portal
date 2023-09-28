from datetime import datetime, timezone  # noqa: D100

from django.contrib import admin

from portal.capstone import models


@admin.register(models.Capstone)
class CapstoneAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ("name",)
    fields = (
        "name",
        "scoring",
        "report_1_provisory_open",
        "report_1_final_open",
        "report_2_provisory_open",
        "report_2_final_open",
    )


@admin.register(models.Report)
class ReportAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ("capstone", "user", "type")
    fields = ("capstone", "user", "type", "file", "submited_at")


@admin.register(models.StudentApi)
class StudentApiAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ("capstone", "user", "url")
    fields = ("capstone", "user", "url")


@admin.register(models.Simulator)
class SimulatorAdmin(admin.ModelAdmin):  # noqa: D101
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
class DatapointAdmin(admin.ModelAdmin):  # noqa: D101
    list_display = ("id", "simulator", "data", "outcome")
    fields = ("simulator", "data", "outcome")
    list_filter = ("simulator",)


class OldFilter(admin.SimpleListFilter):  # noqa: D101
    title = "Old"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "old"

    def lookups(self, request, model_admin):  # noqa: D102
        return (("now", "now"),)

    def queryset(self, request, queryset):  # noqa: D102
        if self.value() == "now":
            return queryset.filter(due__lte=datetime.now(timezone.utc))
        return None


@admin.register(models.DueDatapoint)
class DueDatapointAdmin(admin.ModelAdmin):  # noqa: D101
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
