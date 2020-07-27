import random
import string
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.utils import timezone


def random_path(instance, filename):
    date = str(timezone.now()).split(' ')[0]
    randstr = "".join(random.choices(string.ascii_lowercase, k=12))
    return (f'{instance.code}_{filename}'
            f'_{date}_{randstr}')


class Hackathon(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(default=timezone.now)

    status_choices = (
        ('closed', 'Closed'),
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
    can_submit = ('submissions_open', 'complete')
    can_submit_instructor = ('closed', 'submissions_open', 'complete')

    status = models.CharField(max_length=255,
                              choices=status_choices,
                              default='closed')

    max_submissions = models.IntegerField(default=3)
    team_size = models.IntegerField(default=3)
    max_team_size = models.IntegerField(default=6)
    max_teams = models.IntegerField(default=13)

    script_file = models.FileField(upload_to=random_path,
                                   null=True, blank=True)
    data_file = models.FileField(upload_to=random_path, null=True, blank=True)
    descending = models.BooleanField(blank=True)


class Attendance(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='attendance')
    student = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='attendance')
    present = models.BooleanField(default=True)
    # remote = models.BooleanField(default=False)


class Team(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='teams')
    hackathon_team_id = models.IntegerField(default=0)
    # remote = models.BooleanField(default=False)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      related_name='hackathon_teams')
    name = models.TextField(blank=True)
    logo = models.TextField(blank=True)


class Submission(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='submissions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    score = models.FloatField(default=0.)
    created = models.DateTimeField(auto_now_add=True)
