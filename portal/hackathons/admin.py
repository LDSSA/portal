from django.contrib import admin
from django.contrib.auth import get_user_model

from portal.hackathons import models


@admin.register(models.Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status")
    fields = (
        "status",
        "code",
        "name",
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
            models.Attendance.objects.get_or_create(
                hackathon=obj, user=student
            )


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "hackathon_team_id",
        "name",
        # 'remote',
        "hackathon",
    )
    list_filter = ("hackathon",)


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
    list_display = ("hackathon", "content_object", "score", "created")
    fields = (
        "hackathon",
        "content_object",
        "score",
        "created",
    )
    list_filter = ("hackathon",)
