from django.contrib import admin

from .models import Selection, SelectionDocument, SelectionLogs


class AdminSelection(admin.ModelAdmin):
    list_display = ("user", "status")
    search_fields = ("user__email", "user__uuid", "status")


class AdminSelectionDocument(admin.ModelAdmin):
    list_display = ("selection",)
    search_fields = ("selection__user__email", "selection__user__uuid")


class AdminSelectionLogs(admin.ModelAdmin):
    search_fields = ("selection__user__email", "selection__user__uuid")


admin.site.register(Selection, AdminSelection)
admin.site.register(SelectionDocument, AdminSelectionDocument)
admin.site.register(SelectionLogs, AdminSelectionLogs)
