from django.contrib import admin

from .models import Application, Submission


class AdminApplications(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__email", "user__uuid")


class AdminSubmissions(admin.ModelAdmin):
    list_display = ("application",)
    search_fields = ("application__user__email", "application__user__uuid")


admin.site.register(Application, AdminApplications)
admin.site.register(Submission, AdminSubmissions)
