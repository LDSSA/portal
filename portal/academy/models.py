from django.db import models
from django.conf import settings


class Specialization(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


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
    open = models.BooleanField(default=False)

    checksum = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.specialization.code}/{self.code}"


def notebook_path(instance, filename):
    return '{instance.student.username}_{instance.unit.code}.ipynb'


class Grade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='grades')
    unit = models.ForeignKey(Unit,
                             on_delete=models.CASCADE,
                             related_name='grades')
    score = models.FloatField(null=True)
    notebook = models.FileField(upload_to=notebook_path, null=True)

    STATUSES = (
        ('never-submitted', 'Unsubmitted'),
        ('grading', "Grading"),
        ('failed', "Grading failed"),
        ('out-of-date', "Out-of-date"),
        ('graded', 'Graded'),
    )
    status = models.CharField(
        max_length=1024,
        choices=STATUSES,
        default='never-submitted')
    message = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'unit')

