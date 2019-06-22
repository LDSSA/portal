from django.contrib import admin
from django.contrib.auth import get_user_model

from portal.hackathons import models


@admin.register(models.Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status')
    fields = (
        'status',
        'code',
        'name',
        'max_submissions',
        'team_size',
        'max_team_size',
        'max_teams',
        'y_true',
        'scoring_fcn',
        'descending'
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for student in get_user_model().objects.filter(student=True):
            models.Attendance.objects.get_or_create(hackathon=obj,
                                                    student=student)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('hackathon_team_id', 'name', 'remote', 'hackathon')
    list_filter = ('hackathon', )


@admin.register(models.Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('hackathon', 'student', 'will_attend', 'present', 'remote')
    fields = (
        'hackathon',
        'student',
        'will_attend',
        'present',
        'remote',
    )
    list_filter = ('hackathon', 'will_attend', 'remote')

