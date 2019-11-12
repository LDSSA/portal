import logging
from datetime import datetime, timezone

from django.db import models
from django.conf import settings

from portal.users.models import User


logger = logging.getLogger(__name__)


class Capstone(models.Model):
    name = models.CharField(max_length=1024)
    simulators = models.ManyToManyField('Simulator')


class Score(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    student = models.ForeignKey(User, models.CASCADE)
    score = models.FloatField(default=0)


class Simulator(models.Model):
    name = models.CharField(max_length=1024)
    started = models.DateTimeField(null=True)
    ends = models.DateTimeField(null=True)
    interval = models.DurationField(null=True)
    # example 'https://{app_name}.herokuapp.com/predict'
    endpoint = models.CharField(max_length=255)

    STATUS_CHOICES = (
        ('stopped', 'stopped'),
        ('start', 'start'),
        ('started', 'started'),
        ('paused', 'paused'),
        ('reset', 'reset'),
        ('ended', 'ended'),
    )
    status = models.CharField(choices=STATUS_CHOICES,
                              default='queued',
                              max_length=64)

    def start(self):
        if self.status == 'start':  # Started manually through the admin
            now = datetime.now(timezone.utc)
            self.started = now
            self.status = 'started'
            self.save()

            self.create_due_datapoints(now)

    def create_due_datapoints(self, starts, ends=None):
        self.due_datapoints.all().delete()
        datapoints = self.datapoints.all()
        students = User.objects.filter(student=True)
        due_datapoints = []

        if ends is None:
            ends = self.ends

        interval = (ends - starts) / datapoints.count()
        self.interval = interval

        # Assuming one producer we are queueing BLOCK_SIZE requests per cycle
        # to queue enough requests we need to queue at least
        # (PRODUCER_INTERVAL / interval) * number of students
        if (settings.BLOCK_SIZE
                < students.count() * (settings.PRODUCER_INTERVAL / interval)):
            logger.critical("Current BLOCK_SIZE and PRODUCER_INTERVAL settings"
                            "are not enough")
        self.save()

        for student in students:
            due = starts
            for datapoint in datapoints:
                due_datapoints.append(
                    DueDatapoint(
                        simulator=self,
                        datapoint=datapoint,
                        student=student,
                        due=due,
                    )
                )
                due += interval

        DueDatapoint.objects.bulk_create(due_datapoints)

    def reset(self):
        if self.status == 'reset':
            self.due_datapoints.all().delete()
            self.status = 'stopped'
            self.save()

    def pause(self):
        self.status = 'paused'
        self.save()

    def unpause(self):
        self.status = 'started'
        self.save()


class Datapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE,
                                  related_name='datapoints')
    data = models.TextField()


class DueDatapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE,
                                  related_name='due_datapoints')
    datapoint = models.ForeignKey(Datapoint, models.CASCADE)
    student = models.ForeignKey(User, models.CASCADE)

    due = models.DateTimeField(null=True)
    STATE_CHOICES = (
        ('due', 'due'),
        ('queued', 'queued'),
        ('success', 'success'),
        ('fail', 'fail'),
    )
    state = models.CharField(choices=STATE_CHOICES,
                             default='duw',
                             max_length=64)

    response_content = models.TextField(blank=True)
    response_exception = models.TextField(null=True)
    response_traceback = models.TextField(null=True)
    response_elapsed = models.FloatField(null=True)
    response_status = models.IntegerField(null=True)
    response_timeout = models.BooleanField(default=False)

