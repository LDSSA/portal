import logging
from datetime import datetime, timezone

from django.db import models
from django.conf import settings

from portal.users.models import User


logger = logging.getLogger(__name__)


class Capstone(models.Model):
    name = models.CharField(max_length=1024)

    def __str__(self):
        return self.name


class StudentApp(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    student = models.ForeignKey(User, models.CASCADE)
    app_name = models.CharField(max_length=255, blank=True)


class Score(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    student = models.ForeignKey(User, models.CASCADE)
    score = models.FloatField(default=0)


class Simulator(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)

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
            logger.info("Starting simulator %s", self)
            now = datetime.now(timezone.utc)
            self.started = now
            self.status = 'started'
            self.save()

            self.create_due_datapoints(now)

    def create_due_datapoints(self, starts, ends=None):
        logger.info("Creating due datapoints for %s", self)
        self.due_datapoints.all().delete()
        datapoints = self.datapoints.all()
        students = StudentApp.objects.filter(capstone=self.capstone).exclude(app_name='')
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
            app = StudentApp.objects.get(capstone=self.capstone,
                                         student=student)
            due = starts
            url = self.endpoint.format(app.app_name)
            for datapoint in datapoints:
                due_datapoints.append(
                    DueDatapoint(
                        simulator=self,
                        datapoint=datapoint,
                        student=student,
                        due=due,
                        url=url,
                    )
                )
                due += interval

        logger.info("Creating due datapoints for %s", self)
        DueDatapoint.objects.bulk_create(due_datapoints)

    def __str__(self):
        return self.name

    def reset(self):
        if self.status == 'reset':
            logger.info("Resetting simulator %s", self)
            self.due_datapoints.all().delete()
            self.status = 'stopped'
            self.save()

    def pause(self):
        if self.status == 'pause':
            logger.info("Pausing simulator %s", self)
            self.status = 'paused'
            self.save()

    def resume(self):
        if self.status == 'paused':
            logger.info("Resuming simulator %s", self)
            self.status = 'started'
            self.save()


class Datapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE,
                                  related_name='datapoints')
    data = models.TextField()


class DueDatapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE,
                                  related_name='due_datapoints')
    url = models.TextField()
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

