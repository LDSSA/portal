from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings


class Specialization(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)


class Unit(models.Model):
    specialization = models.ForeignKey(Specialization,
                                       on_delete=models.CASCADE,
                                       related_name='units')

    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE)
    due_date = models.DateField(auto_now_add=True)


class Grade(models.Model):
    student = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit,
                             on_delete=models.CASCADE,
                             related_name='grades')
    grade = models.FloatField(null=True)

