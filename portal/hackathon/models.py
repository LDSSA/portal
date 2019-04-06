from django.db import models
from django.conf import settings


class Hackathon(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)

    student = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     on_delete=models.CASCADE,
                                     through='Attendance')
    will_attend = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         on_delete=models.CASCADE,
                                         related_name='hackathon_will_attend')
    attended = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE,
                                      related_name='hackathon_attended')


class Attendance(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    will_attend = models.BooleanField(default=False)
    present = models.BooleanField(default=False)
    remote = models.BooleanField(default=False)


class Team(models.Model):
    hackathon = models.ForeignKey(Hackathon,
                                  on_delete=models.CASCADE,
                                  related_name='grades')
    students = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE,
                                      related_name='hackathon_teams')
