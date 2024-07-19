from datetime import datetime, timedelta, timezone  # noqa: D100

import pytest
from applications.domain import (
    ApplicationStatus,
    Domain,
    DomainExceptionError,
    SubmissionStatus,
)
from applications.models import Application, Submission, SubmissionTypes
from django.test import TestCase
from interface import interface
from users.models import User

LISBON_TZ = timezone.utc


class TestDomain(TestCase):  # noqa: D101
    def setUp(self) -> None:  # noqa: ANN101, D102, N802
        self.aod = datetime.now(LISBON_TZ) - timedelta(minutes=30)
        self.acd = datetime.now(LISBON_TZ) + timedelta(minutes=30)
        interface.feature_flag_client.set_applications_opening_date(self.aod)
        interface.feature_flag_client.set_applications_closing_date(self.acd)

    def test_get_start_date(self) -> None:  # noqa: ANN101, D102
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        assert Domain.get_start_date(a, SubmissionTypes.coding_test) is None  # noqa: S101
        assert Domain.get_start_date(a, SubmissionTypes.slu01) == self.aod  # noqa: S101
        assert Domain.get_start_date(a, SubmissionTypes.slu02) == self.aod  # noqa: S101
        assert Domain.get_start_date(a, SubmissionTypes.slu03) == self.aod  # noqa: S101

        dt_now = datetime.now(LISBON_TZ)
        a.coding_test_started_at = dt_now
        a.save()
        assert Domain.get_start_date(a, SubmissionTypes.coding_test) == dt_now  # noqa: S101

    def test_get_close_date(self) -> None:  # noqa: ANN101, D102
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        expected_domain_buffer_delta = timedelta(minutes=2)

        assert Domain.get_end_date(a, SubmissionTypes.coding_test) == self.acd  # noqa: S101
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.coding_test, apply_buffer=True)
            == self.acd + expected_domain_buffer_delta
        )  # noqa: S101

        assert Domain.get_end_date(a, SubmissionTypes.slu01) == self.acd  # noqa: S101
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.slu01, apply_buffer=True)
            == self.acd + expected_domain_buffer_delta
        )  # noqa: S101

        assert Domain.get_end_date(a, SubmissionTypes.slu02) == self.acd  # noqa: S101
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.slu02, apply_buffer=True)
            == self.acd + expected_domain_buffer_delta
        )  # noqa: S101

        assert Domain.get_end_date(a, SubmissionTypes.slu03) == self.acd  # noqa: S101
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.slu03, apply_buffer=True)
            == self.acd + expected_domain_buffer_delta
        )  # noqa: S101

        coding_test_delta = timedelta(
            minutes=interface.feature_flag_client.get_coding_test_duration(),
        )
        dt_now = datetime.now(LISBON_TZ)
        a.coding_test_started_at = dt_now
        a.save()
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.coding_test) == dt_now + coding_test_delta
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_end_date(a, SubmissionTypes.coding_test, apply_buffer=True)
            == dt_now + coding_test_delta + expected_domain_buffer_delta
        )  # noqa: S101

    def test_get_best_score(self) -> None:  # noqa: ANN101, D102
        target_app = Application.objects.create(user=User.objects.create(email="target@test.com"))
        other_app = Application.objects.create(user=User.objects.create(email="other@test.com"))
        Submission.objects.create(
            application=target_app,
            score=10,
            submission_type=SubmissionTypes.coding_test.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=89,
            submission_type=SubmissionTypes.coding_test.uname,
        )

        Submission.objects.create(
            application=target_app,
            score=73,
            submission_type=SubmissionTypes.slu01.uname,
        )

        Submission.objects.create(
            application=target_app,
            score=71,
            submission_type=SubmissionTypes.slu03.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=21,
            submission_type=SubmissionTypes.slu03.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=92,
            submission_type=SubmissionTypes.slu03.uname,
        )

        assert (  # noqa: S101
            Domain.get_best_score(target_app, SubmissionTypes.coding_test) == 89  # noqa: PLR2004
        )  # noqa: PLR2004, S101
        assert Domain.get_best_score(target_app, SubmissionTypes.slu01) == 73  # noqa: PLR2004, S101
        assert Domain.get_best_score(target_app, SubmissionTypes.slu02) is None  # noqa: S101
        assert Domain.get_best_score(target_app, SubmissionTypes.slu03) == 92  # noqa: PLR2004, S101

        assert Domain.get_best_score(other_app, SubmissionTypes.coding_test) is None  # noqa: S101
        assert Domain.get_best_score(other_app, SubmissionTypes.slu01) is None  # noqa: S101
        assert Domain.get_best_score(other_app, SubmissionTypes.slu02) is None  # noqa: S101
        assert Domain.get_best_score(other_app, SubmissionTypes.slu03) is None  # noqa: S101

    def test_has_positive_score(self) -> None:  # noqa: ANN101, D102
        target_app = Application.objects.create(user=User.objects.create(email="target@test.com"))
        other_app = Application.objects.create(user=User.objects.create(email="other@test.com"))
        Submission.objects.create(
            application=target_app,
            score=10,
            submission_type=SubmissionTypes.coding_test.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=89,
            submission_type=SubmissionTypes.coding_test.uname,
        )

        Submission.objects.create(
            application=target_app,
            score=15,
            submission_type=SubmissionTypes.slu01.uname,
        )

        Submission.objects.create(
            application=target_app,
            score=14,
            submission_type=SubmissionTypes.slu03.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=5,
            submission_type=SubmissionTypes.slu03.uname,
        )
        Submission.objects.create(
            application=target_app,
            score=19,
            submission_type=SubmissionTypes.slu03.uname,
        )

        assert (  # noqa: S101
            Domain.has_positive_score(target_app, SubmissionTypes.coding_test) is True
        )  # noqa: S101
        assert Domain.has_positive_score(target_app, SubmissionTypes.slu01) is False  # noqa: S101
        assert Domain.has_positive_score(target_app, SubmissionTypes.slu02) is False  # noqa: S101
        assert Domain.has_positive_score(target_app, SubmissionTypes.slu03) is True  # noqa: S101

        assert (  # noqa: S101
            Domain.has_positive_score(other_app, SubmissionTypes.coding_test) is False
        )  # noqa: S101
        assert Domain.has_positive_score(other_app, SubmissionTypes.slu01) is False  # noqa: S101
        assert Domain.has_positive_score(other_app, SubmissionTypes.slu02) is False  # noqa: S101
        assert Domain.has_positive_score(other_app, SubmissionTypes.slu03) is False  # noqa: S101

    def test_add_submission_error_close_applications(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(hours=5),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) - timedelta(hours=2),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu01, Submission())

    def test_add_submission_error_not_started_coding_test(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        a.coding_test_started_at = None
        a.save()
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        assert a.submissions.count() == 0  # noqa: S101

    def test_add_submission_error_not_started(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=60),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu01, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu02, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu03, Submission())

        assert a.submissions.count() == 0  # noqa: S101

    def test_add_submission_error_already_ended_coding_test(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        a.coding_test_started_at = datetime.now(LISBON_TZ) - timedelta(hours=3)
        a.save()

        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        assert a.submissions.count() == 0  # noqa: S101

    def test_add_submission_error_already_ended(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=60),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu01, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu02, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu03, Submission())

        assert a.submissions.count() == 0  # noqa: S101

    def test_add_submission_error_max_submissions(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        for _ in range(251):
            Submission.objects.create(
                application=a,
                submission_type=SubmissionTypes.coding_test.uname,
            )
            Submission.objects.create(application=a, submission_type=SubmissionTypes.slu01.uname)
            Submission.objects.create(application=a, submission_type=SubmissionTypes.slu02.uname)
            Submission.objects.create(application=a, submission_type=SubmissionTypes.slu03.uname)

        a.coding_test_started_at = datetime.now(LISBON_TZ)
        a.save()

        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu01, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu02, Submission())
        with pytest.raises(DomainExceptionError):
            Domain.add_submission(a, SubmissionTypes.slu03, Submission())

        assert a.submissions.count() == 251 * 4  # noqa: S101

    def test_add_submission(self) -> None:  # noqa: ANN101, D102
        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=30),
        )
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        a.coding_test_started_at = datetime.now(LISBON_TZ)
        a.save()

        Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        Domain.add_submission(a, SubmissionTypes.slu01, Submission())
        Domain.add_submission(a, SubmissionTypes.slu02, Submission())
        Domain.add_submission(a, SubmissionTypes.slu03, Submission())
        assert a.submissions.count() == 4  # noqa: PLR2004, S101

        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=30),
        )
        # will work because end-date will be based on start_end + duration,
        # not on the ff.closing_date
        Domain.add_submission(a, SubmissionTypes.coding_test, Submission())
        assert a.submissions.count() == 5  # noqa: PLR2004, S101

    def test_get_status(self) -> None:  # noqa: ANN101, D102
        a = Application.objects.create(user=User.objects.create(email="target@test.com"))

        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=5),
        )
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.coding_test)
            == SubmissionStatus.not_started
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu01) == SubmissionStatus.not_started
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu02) == SubmissionStatus.not_started
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu03) == SubmissionStatus.not_started
        )  # noqa: S101
        assert Domain.get_application_status(a) == ApplicationStatus.not_started  # noqa: S101

        interface.feature_flag_client.set_applications_opening_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=5),
        )
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) + timedelta(minutes=5),
        )
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.coding_test)
            == SubmissionStatus.not_started
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu01) == SubmissionStatus.ongoing
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu02) == SubmissionStatus.ongoing
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu03) == SubmissionStatus.ongoing
        )  # noqa: S101
        assert Domain.get_application_status(a) == ApplicationStatus.ongoing  # noqa: S101

        Submission.objects.create(
            application=a,
            score=99,
            submission_type=SubmissionTypes.slu01.uname,
        )
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu01) == SubmissionStatus.passed
        )  # noqa: S101
        assert Domain.get_application_status(a) == ApplicationStatus.ongoing  # noqa: S101

        Submission.objects.create(
            application=a,
            score=99,
            submission_type=SubmissionTypes.coding_test.uname,
        )
        Submission.objects.create(
            application=a,
            score=99,
            submission_type=SubmissionTypes.slu01.uname,
        )
        slu02_sub = Submission.objects.create(
            application=a,
            score=99,
            submission_type=SubmissionTypes.slu02.uname,
        )
        Submission.objects.create(
            application=a,
            score=99,
            submission_type=SubmissionTypes.slu03.uname,
        )

        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.coding_test) == SubmissionStatus.passed
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu01) == SubmissionStatus.passed
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu02) == SubmissionStatus.passed
        )  # noqa: S101
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu02) == SubmissionStatus.passed
        )  # noqa: S101
        assert Domain.get_application_status(a) == ApplicationStatus.passed  # noqa: S101

        slu02_sub.delete()
        interface.feature_flag_client.set_applications_closing_date(
            datetime.now(LISBON_TZ) - timedelta(minutes=5),
        )
        a.save()
        assert (  # noqa: S101
            Domain.get_sub_type_status(a, SubmissionTypes.slu02) == SubmissionStatus.failed
        )  # noqa: S101
        assert Domain.get_application_status(a) == ApplicationStatus.failed  # noqa: S101
