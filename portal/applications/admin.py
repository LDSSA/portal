from django.contrib import admin

from .models import Application, Challenge, Submission


class AdminApplications(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__email", "user__uuid")


class AdminSubmissions(admin.ModelAdmin):
    list_display = ("pk", "user", "application", "unit")
    search_fields = ("application__user__email", "application__user__uuid")


class AdminChallenge(admin.ModelAdmin):
    list_display = ("code", "max_score", "pass_score")


admin.site.register(Application, AdminApplications)
admin.site.register(Submission, AdminSubmissions)
admin.site.register(Challenge, AdminChallenge)
