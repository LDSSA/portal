import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

from django.db import models
from django.conf import settings

from portal.hackathons.models import random_path
from portal.users.models import User


logger = logging.getLogger(__name__)


class Capstone(models.Model):
    name = models.CharField(max_length=1024)

    scoring = models.FileField(upload_to=random_path,
                               null=True, blank=True)

    def __str__(self):
        return self.name

    def score(self):
        # Load scoring
        glob = {}
        script = self.scoring.read().decode()
        exec(script, glob)

        for api in self.studentapi_set.all():
            # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
            score = glob['score'](self, api)
            api.score = score
            api.save()


class StudentApi(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    student = models.ForeignKey(User, models.CASCADE)
    url = models.CharField(max_length=255, blank=True)
    score = models.FloatField(default=0)


class Simulator(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)

    name = models.CharField(max_length=1024)
    started = models.DateTimeField(null=True)
    ends = models.DateTimeField(null=True)
    interval = models.DurationField(null=True)
    # example: predict
    path = models.CharField(max_length=255)

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
            logger.info("Starting simulator: %s", self)
            now = datetime.now(timezone.utc)
            self.started = now
            self.status = 'started'
            self.save()

            self.create_due_datapoints(now)

    def create_due_datapoints(self, starts):
        logger.info("Creating due datapoints for %s", self)
        self.due_datapoints.all().delete()
        datapoints = self.datapoints.all()
        student_apis = (StudentApi.objects
                        .filter(capstone=self.capstone)
                        .exclude(url=''))

        interval = (self.ends - starts) / datapoints.count()

        # Assuming one producer we are queueing BLOCK_SIZE requests per cycle
        # to queue enough requests we need to queue at least
        # (PRODUCER_INTERVAL / interval) * number of students
        required_requests_per_cycle = (
            student_apis.count()
            * (settings.PRODUCER_INTERVAL / interval.total_seconds()))
        logger.debug('Block size: %s', settings.BLOCK_SIZE)
        logger.debug('Required requests: %s', required_requests_per_cycle)
        if settings.BLOCK_SIZE < required_requests_per_cycle:
            raise RuntimeError(
                f'Number of queued requests per cycle is not enough, '
                f'required {required_requests_per_cycle}',
                f'consumed {settings.BLOCK_SIZE}',
            )

        self.interval = interval
        self.save()

        for student_api in student_apis:
            self.add_student_api(student_api,
                                 datapoints,
                                 starts)

    def add_student_api(self, student_api, datapoints, starts=None):
        logger.info("Creating due datapoints for simulator %s student %s",
                    self, student_api.student)
        due = starts or datetime.now(timezone.utc)
        interval = (self.ends - starts) / datapoints.count()

        logger.debug("Starting: %s", due)
        logger.debug("Ending: %s", self.ends)
        logger.debug("Count: %s", datapoints.count())
        logger.debug("Interval: %s", interval)

        url = urljoin(student_api.url, self.path)
        due_datapoints = []
        for datapoint in datapoints:
            due_datapoints.append(
                DueDatapoint(
                    simulator=self,
                    datapoint=datapoint,
                    student=student_api.student,
                    due=due,
                    url=url,
                )
            )
            due += interval
        DueDatapoint.objects.bulk_create(due_datapoints)

    def __str__(self):
        return self.name

    def reset(self):
        if self.status == 'reset':
            logger.info("Resetting simulator %s", self)
            self.due_datapoints.all().delete()
            self.status = 'stopped'
            self.save()


class Datapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE,
                                  related_name='datapoints')
    data = models.TextField(blank=True)
    outcome = models.TextField(blank=True)


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
                             default='due',
                             max_length=64)

    response_content = models.TextField(blank=True)
    response_exception = models.TextField(blank=True)
    response_traceback = models.TextField(blank=True)
    response_elapsed = models.FloatField(null=True)
    response_status = models.IntegerField(null=True)
    response_timeout = models.BooleanField(default=False)
