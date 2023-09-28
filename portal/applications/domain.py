from datetime import datetime, timedelta, timezone  # noqa: D100
from enum import Enum
from logging import getLogger
from typing import Any

from constance import config
from django.db import models

from portal.admissions import emails
from portal.applications.models import Application, Challenge, Submission

logger = getLogger(__name__)


class Status(Enum):  # noqa: D101
    not_started = "Not Started"
    ongoing = "Ongoing"
    passed = "Passed"
    failed = "Failed"


ApplicationStatus = Status
SubmissionStatus = Status


class DomainException(Exception):  # noqa: D101
    pass


class Domain:  # noqa: D101
    # a candidate is only allowed to get graded MAX_SUBMISSIONS of times per submission type
    max_submissions = 250

    # buffer to upload submissions
    submission_timedelta_buffer = timedelta(minutes=2)

    @classmethod
    def get_application_status(cls, application: Application) -> ApplicationStatus:  # noqa: D102
        return cls.get_application_detailed_status(application)["application"]

    @classmethod
    def get_application_detailed_status(cls, application) -> dict[str, Status]:  # noqa: D102
        chall_status = {}
        for chall in Challenge.objects.all():
            chall_status[chall.code] = cls.get_sub_type_status(application, chall)

        application_status = None
        if any((s == SubmissionStatus.failed for _, s in chall_status.items())):
            application_status = ApplicationStatus.failed
        elif any((s == SubmissionStatus.ongoing for _, s in chall_status.items())):
            application_status = ApplicationStatus.ongoing
        elif all((s == SubmissionStatus.passed for _, s in chall_status.items())):
            application_status = ApplicationStatus.passed
        elif all((s == SubmissionStatus.not_started for _, s in chall_status.items())):
            application_status = ApplicationStatus.not_started
        else:
            # some tests passed, some not started
            application_status = ApplicationStatus.ongoing

        return {"application": application_status, **chall_status}

    @classmethod
    def get_sub_type_status(cls, application, challenge):  # noqa: D102
        if cls.has_positive_score(application, challenge):
            return SubmissionStatus.passed

        dt_now = datetime.now(timezone.utc)
        start_date = cls.get_start_date(application, challenge)
        end_date = cls.get_end_date(application, challenge)

        if end_date < dt_now:
            return SubmissionStatus.failed

        if start_date is None or start_date > dt_now:
            return SubmissionStatus.not_started

        return SubmissionStatus.ongoing

    @staticmethod
    def get_start_date(application, challenge):  # noqa: D102
        if challenge.code == "coding_test":
            start_date = getattr(application, f"{challenge.code}_started_at", None)
        else:
            start_date = config.ADMISSIONS_APPLICATIONS_START

        return start_date

    @classmethod
    def get_end_date(cls, application, challenge, *, apply_buffer=False):  # noqa: D102
        start_date = cls.get_start_date(application, challenge)

        if challenge.code == "coding_test":
            if start_date is not None:
                close_date = start_date + config.ADMISSIONS_CODING_TEST_DURATION
            else:
                close_date = config.ADMISSIONS_SELECTION_START
        else:
            close_date = config.ADMISSIONS_SELECTION_START

        if apply_buffer:
            # buffer is applied to account for possible latency (lambda grader func may take a while)
            return close_date + cls.submission_timedelta_buffer

        return close_date

    @staticmethod
    def get_best_score(application, challenge):  # noqa: D102
        return Submission.objects.filter(application=application, unit=challenge).aggregate(
            models.Max("score")
        )["score__max"]

    @classmethod
    def has_positive_score(cls, application, challenge):  # noqa: D102
        score = cls.get_best_score(application, challenge)
        return score is not None and score >= challenge.pass_score

    @classmethod
    def can_add_submission(cls, application, challenge):  # noqa: D102
        if config.PORTAL_STATUS != "admissions:applications":
            return False

        dt_now = datetime.now(timezone.utc)
        start_dt = Domain.get_start_date(application, challenge)

        if start_dt is None:
            return False

        if dt_now < start_dt:
            return False

        if dt_now > Domain.get_end_date(application, challenge, apply_buffer=True):
            return False

        if (
            Submission.objects.filter(application=application, unit=challenge).count()
            >= cls.max_submissions
        ):
            logger.warning(f"user `{application.user.email}` reached max submissions.")
            return False

        return True

    @classmethod
    def add_submission(cls, application, challenge, sub):  # noqa: D102
        if not cls.can_add_submission(application, challenge):
            raise DomainException("Can't add submission")

        sub.application = application
        sub.challenge = challenge
        sub.save()

    @staticmethod
    def application_over(application: Application) -> None:  # noqa: D102
        if application.application_over_email_sent is not None:
            raise DomainException("email was already sent")

        to_name = application.user.name

        status = Domain.get_application_status(application)
        if status == ApplicationStatus.passed:
            emails.send_application_is_over_passed(to_email=application.user.email, to_name=to_name)
            application.application_over_email_sent = "passed"
            application.save()

        else:
            emails.send_application_is_over_failed(to_email=application.user.email, to_name=to_name)
            application.application_over_email_sent = "failed"
            application.save()

    @staticmethod
    def get_candidate_release_zip(sub_type_uname: str) -> str:  # noqa: D102
        return f"candidate-dist/candidate-release-{sub_type_uname}.zip"


class DomainQueries:  # noqa: D101
    @staticmethod
    def all() -> Any:  # noqa: D102
        return Application.objects.all()

    @staticmethod
    def applications_count() -> int:  # noqa: D102
        return DomainQueries.all().count()

    @staticmethod
    def applications_with_sent_emails_count() -> int:  # noqa: D102
        return Application.objects.filter(application_over_email_sent__isnull=False).count()
