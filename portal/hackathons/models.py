import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone


class Hackathon(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(default=timezone.now)

    status_choices = (
        ('closed', 'Closed'),
        ('taking_attendance', 'Taking Attendance'),
        ('attendance_closed', 'Attendance Closed'),
        ('marking_presences', 'Marking Presences'),
        ('generating_teams', 'Generating Teams'),
        ('ready', 'Ready'),
        ('submissions_open', 'Submissions Open'),
        ('submissions_closed', 'Submissions Closed'),
        ('complete', 'Complete'),
    )
    teams_exist = ('generating_teams',
                   'ready',
                   'submissions_open',
                   'submissions_closed',
                   'complete')
    teams_ready = ('ready',
                   'submissions_open',
                   'submissions_closed',
                   'complete')
    can_update_team_data = ('ready',
                            'submissions_open')

    status = models.CharField(max_length=255,
                              choices=status_choices,
                              default='closed')

    max_submissions = models.IntegerField(default=3)
    team_size = models.IntegerField(default=3)
    max_team_size = models.IntegerField(default=6)
    max_teams = models.IntegerField(default=13)

    scoring_fcn = models.TextField(blank=True)
    y_true = models.TextField(blank=True)
    descending = models.BooleanField(blank=True)


class Attendance(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='attendance')
    student = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='attendance')
    will_attend = models.BooleanField(default=False)
    present = models.BooleanField(default=False)
    remote = models.BooleanField(default=False)


class Team(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='teams')
    hackathon_team_id = models.IntegerField(default=0)
    remote = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      related_name='hackathon_teams')
    name = models.TextField(blank=True)
    logo = models.TextField(blank=True)

    submissions = models.IntegerField(default=0)
    score = models.FloatField(default=0.)
