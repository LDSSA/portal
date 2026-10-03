from django.contrib import admin

from .models import EnrollmentEmail, Selection, SelectionDocument, SelectionLogs


class ReadOnlyAdmissionAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AdminSelection(ReadOnlyAdmissionAdmin):
    list_display = ("user", "status", "scholarship_status")
    list_filter = ("user__admissions_mode", "status", "scholarship_status")
    search_fields = ("user__email", "user__username", "user__id", "status")


class AdminSelectionDocument(ReadOnlyAdmissionAdmin):
    list_display = ("selection",)
    search_fields = (
        "selection__user__email",
        "selection__user__username",
        "selection__user__id",
    )


class AdminSelectionLogs(ReadOnlyAdmissionAdmin):
    search_fields = (
        "selection__user__email",
        "selection__user__username",
        "selection__user__id",
    )


admin.site.register(Selection, AdminSelection)
admin.site.register(SelectionDocument, AdminSelectionDocument)
admin.site.register(SelectionLogs, AdminSelectionLogs)


@admin.register(EnrollmentEmail)
class EnrollmentEmailAdmin(ReadOnlyAdmissionAdmin):
    list_display = (
        "recipient",
        "subject",
        "created_at",
        "sent_at",
        "attempts",
        "next_attempt_at",
    )
    list_filter = ("sent_at",)
    search_fields = ("recipient", "event_key")
