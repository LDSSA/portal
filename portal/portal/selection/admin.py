from django.contrib import admin  # noqa: D100

from .models import Selection, SelectionDocument, SelectionLogs


class AdminSelection(admin.ModelAdmin):  # noqa: D101
    list_display = ("user", "status")
    search_fields = ("user__email", "user__username", "user__id", "status")


class AdminSelectionDocument(admin.ModelAdmin):  # noqa: D101
    list_display = ("selection",)
    search_fields = ("selection__user__email", "selection__user__username", "selection__user__id")


class AdminSelectionLogs(admin.ModelAdmin):  # noqa: D101
    search_fields = ("selection__user__email", "selection__user__username", "selection__user__id")


admin.site.register(Selection, AdminSelection)
admin.site.register(SelectionDocument, AdminSelectionDocument)
admin.site.register(SelectionLogs, AdminSelectionLogs)
