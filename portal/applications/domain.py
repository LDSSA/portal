from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger
from typing import Any, Dict, Optional

from django.db import models

from interface import interface
from profiles.models import Profile

from .models import Application, Submission, SubmissionType, SubmissionTypes

logger = getLogger(__name__)


class Status(Enum):
    not_started = "Not Started"
    ongoing = "Ongoing"
    passed = "Passed"
    failed = "Failed"


ApplicationStatus = Status
SubmissionStatus = Status


class DomainException(Exception):
    pass


class Domain:
    # a candidate is only allowed to get graded MAX_SUBMISSIONS of times per submission type
    max_submissions = 250

    # buffer to upload submissions
    submission_timedelta_buffer = timedelta(minutes=2)

    @staticmethod
    def get_application_status(application: Application) -> ApplicationStatus:
        return Domain.get_application_detailed_status(application)[
            "application"
        ]

    @staticmethod
    def get_application_detailed_status(
        application: Application,
    ) -> Dict[str, Status]:
        sub_type_status = {}
        for sub_type in SubmissionTypes.all:
            sub_type_status[sub_type.uname] = Domain.get_sub_type_status(
                application, sub_type
            )

        application_status = None
        if any(
            (s == SubmissionStatus.failed for _, s in sub_type_status.items())
        ):
            application_status = ApplicationStatus.failed
        elif any(
            (s == SubmissionStatus.ongoing for _, s in sub_type_status.items())
        ):
            application_status = ApplicationStatus.ongoing
        elif all(
            (s == SubmissionStatus.passed for _, s in sub_type_status.items())
        ):
            application_status = ApplicationStatus.passed
        elif all(
            (
                s == SubmissionStatus.not_started
                for _, s in sub_type_status.items()
            )
        ):
            application_status = ApplicationStatus.not_started
        else:
            # some tests passed, some not started
            application_status = ApplicationStatus.ongoing

        return {"application": application_status, **sub_type_status}

    @staticmethod
    def get_sub_type_status(
        application: Application, sub_type: SubmissionType
    ) -> SubmissionStatus:
        if Domain.has_positive_score(application, sub_type):
            return SubmissionStatus.passed

        dt_now = datetime.now()
        start_date = Domain.get_start_date(application, sub_type)
        end_date = Domain.get_end_date(application, sub_type)

        if end_date < dt_now:
            return SubmissionStatus.failed

        if start_date is None or start_date > dt_now:
            return SubmissionStatus.not_started

        return SubmissionStatus.ongoing

    @staticmethod
    def get_start_date(
        application: Application, sub_type: SubmissionType
    ) -> Optional[datetime]:
        if sub_type == SubmissionTypes.coding_test:
            start_date = getattr(
                application, f"{sub_type.uname}_started_at", None
            )
        else:
            start_date = (
                interface.feature_flag_client.get_applications_opening_date()
            )

        return start_date

    @staticmethod
    def get_end_date(
        application: Application,
        sub_type: SubmissionType,
        *,
        apply_buffer: bool = False,
    ) -> datetime:
        start_date = Domain.get_start_date(application, sub_type)

        if sub_type == SubmissionTypes.coding_test:
            if start_date is not None:
                close_date = start_date + timedelta(
                    minutes=interface.feature_flag_client.get_coding_test_duration()
                )
            else:
                close_date = (
                    interface.feature_flag_client.get_applications_closing_date()
                )
        else:
            close_date = (
                interface.feature_flag_client.get_applications_closing_date()
            )

        if apply_buffer:
            # buffer is applied to account for possible latency (lambda grader func may take a while)
            return close_date + Domain.submission_timedelta_buffer
        else:
            return close_date

    @staticmethod
    def get_best_score(
        application: Application, sub_type: SubmissionType
    ) -> Optional[int]:
        return Submission.objects.filter(
            application=application, submission_type=sub_type.uname
        ).aggregate(models.Max("score"))["score__max"]

    @staticmethod
    def has_positive_score(
        application: Application, sub_type: SubmissionType
    ) -> bool:
        score = Domain.get_best_score(application, sub_type)
        return score is not None and score >= sub_type.pass_score

    @staticmethod
    def can_add_submission(
        application: Application, sub_type: SubmissionType
    ) -> bool:
        dt_now = datetime.now()

        start_dt = Domain.get_start_date(application, sub_type)

        if start_dt is None:
            return False

        if dt_now < start_dt:
            return False

        if dt_now > Domain.get_end_date(
            application, sub_type, apply_buffer=True
        ):
            return False

        if (
            Submission.objects.filter(
                application=application, submission_type=sub_type.uname
            ).count()
            >= Domain.max_submissions
        ):
            logger.warning(
                f"user `{application.user.email}` reached max submissions."
            )
            return False

        return True

    @staticmethod
    def add_submission(
        application: Application, sub_type: SubmissionType, sub: Submission
    ) -> None:
        if not Domain.can_add_submission(application, sub_type):
            raise DomainException("Can't add submission")

        sub.application = application
        sub.submission_type = sub_type.uname
        sub.save()

    @staticmethod
    def application_over(application: Application) -> None:
        if application.application_over_email_sent is not None:
            raise DomainException("email was already sent")

        try:
            to_name = application.user.profile.name
        except Profile.DoesNotExist:
            to_name = "candidate"

        status = Domain.get_application_status(application)
        if status == ApplicationStatus.passed:
            interface.email_client.send_application_is_over_passed(
                to_email=application.user.email, to_name=to_name
            )
            application.application_over_email_sent = "passed"
            application.save()

        else:
            interface.email_client.send_application_is_over_failed(
                to_email=application.user.email, to_name=to_name
            )
            application.application_over_email_sent = "failed"
            application.save()

    @staticmethod
    def get_candidate_release_zip(sub_type_uname: str) -> str:
        return f"candidate-dist/candidate-release-{sub_type_uname}.zip"


class DomainQueries:
    @staticmethod
    def all() -> Any:
        return Application.objects.all()

    @staticmethod
    def applications_count() -> int:
        return DomainQueries.all().count()

    @staticmethod
    def applications_with_sent_emails_count() -> int:
        return Application.objects.filter(
            application_over_email_sent__isnull=False
        ).count()
