from django.contrib import admin  # noqa: D100

from .models import Application, Challenge, Submission


class AdminApplications(admin.ModelAdmin):  # noqa: D101
    list_display = ("user",)
    search_fields = ("user__email",)


class AdminSubmissions(admin.ModelAdmin):  # noqa: D101
    list_display = ("pk", "user", "application", "unit")
    search_fields = ("application__user__email",)


class AdminChallenge(admin.ModelAdmin):  # noqa: D101
    list_display = ("code", "max_score", "pass_score")


admin.site.register(Application, AdminApplications)
admin.site.register(Submission, AdminSubmissions)
admin.site.register(Challenge, AdminChallenge)
