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

    scoring = models.FileField(upload_to=random_path, null=True, blank=True)

    def __str__(self):
        return self.name

    def score(self):
        # Load scoring
        glob = {}
        script = self.scoring.read().decode()
        exec(script, glob)

        for api in self.studentapi_set.all():
            # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
            score = glob["score"](api)
            api.score = score
            api.save()


class StudentApi(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    url = models.CharField(max_length=255, blank=True)
    score = models.FloatField(default=0)


class Simulator(models.Model):
    capstone = models.ForeignKey(
        Capstone, models.CASCADE, related_name="simulators"
    )

    name = models.CharField(max_length=1024)
    started = models.DateTimeField(null=True)
    ends = models.DateTimeField(null=True)
    interval = models.DurationField(null=True)
    # example: predict
    path = models.CharField(max_length=255)

    STATUS_CHOICES = (
        ("stopped", "stopped"),
        ("start", "start"),
        ("started", "started"),
        ("paused", "paused"),
        ("reset", "reset"),
        ("ended", "ended"),
    )
    status = models.CharField(
        choices=STATUS_CHOICES, default="queued", max_length=64
    )

    def start(self):
        if self.status == "start":  # Started manually through the admin
            logger.info("Starting simulator: %s", self)
            now = datetime.now(timezone.utc)
            self.started = now
            self.status = "started"
            self.save()

            self.create_due_datapoints(now)

    def create_due_datapoints(self, starts):
        logger.info("Creating due datapoints for %s", self)
        self.due_datapoints.all().delete()
        datapoints = self.datapoints.order_by("id").all()
        student_apis = StudentApi.objects.filter(
            capstone=self.capstone
        ).exclude(url="")

        interval = (self.ends - starts) / datapoints.count()
        self.interval = interval
        self.save()

        for student_api in student_apis:
            self.add_student_api(student_api, datapoints, starts)

    def add_student_api(self, student_api, datapoints, starts=None):
        logger.info(
            "Creating due datapoints for simulator %s student %s",
            self,
            student_api.user,
        )
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
                    user=student_api.user,
                    due=due,
                    url=url,
                )
            )
            due += interval
        DueDatapoint.objects.bulk_create(due_datapoints)

    def __str__(self):
        return self.name

    def reset(self):
        if self.status == "reset":
            logger.info("Resetting simulator %s", self)
            self.due_datapoints.all().delete()
            self.status = "stopped"
            self.save()


class Datapoint(models.Model):
    simulator = models.ForeignKey(
        Simulator, models.CASCADE, related_name="datapoints"
    )
    data = models.TextField(blank=True)
    outcome = models.TextField(blank=True)


class DueDatapoint(models.Model):
    simulator = models.ForeignKey(
        Simulator, models.CASCADE, related_name="due_datapoints"
    )
    url = models.TextField()
    datapoint = models.ForeignKey(Datapoint, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    due = models.DateTimeField(null=True)
    STATE_CHOICES = (
        ("queued", "queued"),
        ("success", "success"),
        ("fail", "fail"),
    )
    state = models.CharField(
        choices=STATE_CHOICES, default="queued", max_length=64
    )

    response_content = models.TextField(blank=True)
    response_exception = models.TextField(blank=True)
    response_traceback = models.TextField(blank=True)
    response_elapsed = models.FloatField(null=True)
    response_status = models.IntegerField(null=True)
    response_timeout = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['due', 'state']),
        ]
