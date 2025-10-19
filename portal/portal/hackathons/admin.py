from django.contrib import admin
from django.contrib.auth import get_user_model

from portal.hackathons import models
from portal.users.models import User


@admin.register(models.Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status")
    fields = (
        "status",
        "code",
        "name",
        "due_date",
        "max_submissions",
        "team_size",
        "max_team_size",
        "max_teams",
        "descending",
        "script_file",
        "data_file",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for student in get_user_model().objects.filter(is_student=True):
            models.Attendance.objects.get_or_create(hackathon=obj, user=student)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "hackathon_team_id",
        "name",
        # 'remote',
        "hackathon",
    )
    list_filter = ("hackathon",)
    filter_horizontal = ("users",)


@admin.register(models.Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "hackathon",
        "user",
        "present",
        # 'remote',
    )
    fields = (
        "hackathon",
        "user",
        "present",
        # 'remote',
    )
    list_filter = (
        "hackathon",
        # 'remote',
    )


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "hackathon",
        "get_name",
        "score",
        "created",
    )
    fields = (
        "hackathon",
        "content_object",
        "score",
        "created",
    )
    readonly_fields = (
        "hackathon",
        "created",
        "content_object",
    )
    list_filter = ("hackathon",)

    def get_name(self, obj):
        if isinstance(obj.content_object, User):
            try:
                return f"[{obj.content_object.hackathon_team_id}] {obj.content_object.name}"
            except AttributeError:
                return obj.content_object.username
