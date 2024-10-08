import logging
import random
import string
from datetime import datetime, timezone
from urllib.parse import urljoin

from django.db import models

from portal.hackathons.models import random_path
from portal.users.models import User

logger = logging.getLogger(__name__)


def report_path(instance, filename):
    randstr = "".join(random.choices(string.ascii_lowercase, k=12))
    return f"{instance.user.username}/{instance.type}_{instance.user.username}_{randstr}.pdf"


class Capstone(models.Model):
    name = models.CharField(max_length=1024)

    scoring = models.FileField(upload_to=random_path, null=True, blank=True)
    proposal_open = models.BooleanField(default=False)
    report_provisory_open = models.BooleanField(default=False)
    report_final_open = models.BooleanField(default=False)

    def __str__(self) -> str:
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


class Report(models.Model):
    class Type(models.TextChoices):
        proposal = ("proposal", "Proposal")
        report_provisory = ("report_provisory", "Report Provisory")
        report_final = ("report_final", "Report Final")

    capstone = models.ForeignKey(Capstone, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    type = models.CharField(max_length=32, choices=Type.choices)
    file = models.FileField(upload_to=report_path, null=True, blank=True)
    submited_at = models.DateTimeField(auto_now=True)


class StudentApi(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    url = models.CharField(max_length=255, blank=True)
    score = models.FloatField(default=0)


class Simulator(models.Model):
    capstone = models.ForeignKey(Capstone, models.CASCADE, related_name="simulators")

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
    status = models.CharField(choices=STATUS_CHOICES, default="queued", max_length=64)

    def __str__(self) -> str:
        return self.name

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
        student_apis = StudentApi.objects.filter(capstone=self.capstone).exclude(url="")

        interval = (self.ends - starts) / datapoints.count()
        self.interval = interval
        self.save()

        for student_api in student_apis:
            self.add_student_api(student_api, datapoints, starts)

    def add_student_api(
        self,
        student_api,
        datapoints,
        starts=None,
    ):
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
                ),
            )
            due += interval
        DueDatapoint.objects.bulk_create(due_datapoints)

    def reset(self):
        if self.status == "reset":
            logger.info("Resetting simulator %s", self)
            self.due_datapoints.all().delete()
            self.status = "stopped"
            self.save()


class Datapoint(models.Model):
    simulator = models.ForeignKey(Simulator, models.CASCADE, related_name="datapoints")
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
    state = models.CharField(choices=STATE_CHOICES, default="queued", max_length=64)

    response_content = models.TextField(blank=True)
    response_exception = models.TextField(blank=True)
    response_traceback = models.TextField(blank=True)
    response_elapsed = models.FloatField(null=True)
    response_status = models.IntegerField(null=True)
    response_timeout = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["due", "state"]),
        ]
