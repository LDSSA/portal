from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from constance import config
from constance.test import override_config
from django.core.exceptions import ValidationError
from django.urls import reverse

from portal.academy.models import Grade
from portal.academy.services import (
    check_complete_specialization,
    check_graduation_status,
    unit_deadline,
)
from portal.admissions.policy import (
    new_signups_open,
    payment_window_open,
    registration_changes_open,
)
from portal.hackathons.models import Attendance, Hackathon
from portal.hackathons.services import generate_teams, get_groups

pytestmark = pytest.mark.django_db
LISBON = ZoneInfo("Europe/Lisbon")


def test_optional_and_invalid_grades(student, slu1, slu2, specialization):
    slu2.required_for_certificate = False
    slu2.save()
    grade = Grade.objects.create(
        user=student, unit=slu1, score=20, status="checksum-failed"
    )
    assert not check_complete_specialization(student, specialization)
    grade.status = "graded"
    grade.on_time = False
    grade.save()
    assert not check_complete_specialization(student, specialization)
    grade.on_time = True
    grade.save()
    assert check_complete_specialization(student, specialization)


@pytest.mark.parametrize(
    "day,utc_hour",
    [
        (date(2026, 10, 24), 23),
        (date(2026, 10, 25), 0),
        (date(2027, 3, 27), 0),
        (date(2027, 3, 28), 23),
    ],
)
def test_lisbon_deadlines_include_dst(slu1, day, utc_hour):
    slu1.due_date = day
    assert unit_deadline(slu1).astimezone(dt_timezone.utc).hour == utc_hour


def test_future_hackathons_are_not_absences(student, hackathon1, hackathon2):
    hackathon1.status = "complete"
    hackathon1.save()
    Attendance.objects.create(user=student, hackathon=hackathon1, present=True)
    assert check_graduation_status(student)


@pytest.mark.parametrize("code", ["HCKT01", "HCKT06"])
def test_mandatory_hackathon_absence_loses_certificate(student, code):
    Hackathon.objects.create(code=code, status="complete", descending=False)
    assert not check_graduation_status(student)


def test_late_work_does_not_restore_certificate(student, slu1):
    Grade.objects.create(
        user=student, unit=slu1, status="graded", score=20, on_time=False
    )
    assert not check_graduation_status(student)


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 5, 6, 7, 13, 25])
def test_groups_preserve_students_and_capacity(count):
    groups = get_groups(list(range(count)), 5)
    assert sorted(x for group in groups for x in group) == list(range(count))
    assert all(0 < len(group) <= 5 for group in groups)
    if groups:
        assert max(map(len, groups)) - min(map(len, groups)) <= 1


def test_one_person_team_and_over_capacity(student, student2, hackathon1, grade_slu1):
    student.admissions_mode = "no_exam"
    student.can_attend_next = False
    student.save()
    Attendance.objects.create(user=student, hackathon=hackathon1, present=True)
    generate_teams(hackathon1, 5, 5, 1)
    assert hackathon1.teams.get().users.get() == student
    student2.admissions_mode = "no_exam"
    student2.save()
    Grade.objects.create(user=student2, unit=grade_slu1.unit, status="graded", score=16)
    Attendance.objects.create(user=student2, hackathon=hackathon1, present=True)
    with pytest.raises(ValidationError):
        generate_teams(hackathon1, 1, 1, 1)
    assert hackathon1.teams.count() == 1


def test_closed_or_unreleased_unit_rejects_post(client, student, slu1):
    client.force_login(student)
    slu1.open = False
    slu1.save()
    url = reverse("academy:student-unit-detail", args=[slu1.pk])
    assert client.post(url).status_code == 302
    assert not Grade.objects.exists()
    slu1.open = True
    slu1.available_on = date(2099, 1, 1)
    slu1.save()
    assert client.post(url).status_code == 302
    assert not Grade.objects.exists()


def test_late_no_exam_student_keeps_course_access(client, student, slu1):
    student.admissions_mode = "no_exam"
    student.can_graduate = False
    student.save()
    client.force_login(student)
    with override_config(
        NO_EXAM_ACADEMY_ACCESS_OPEN=True,
        ACADEMY_START=datetime(2020, 1, 1, tzinfo=LISBON),
    ):
        with patch("portal.grading.services.MockGrading.run_grading"):
            response = client.post(
                reverse("academy:student-unit-detail", args=[slu1.pk])
            )
        assert response.status_code == 302
        assert Grade.objects.get().on_time is False
        assert client.get(reverse("academy:student-unit-list")).status_code == 200


def test_calendar_registration_closes_before_payments(student):
    student.admissions_mode = "no_exam"
    with override_config(
        ADMISSIONS_MODE="no_exam",
        ACCOUNT_ALLOW_REGISTRATION=True,
        NO_EXAM_REGISTRATION_OPEN=True,
        NO_EXAM_USE_SCHEDULE=True,
        NO_EXAM_SIGNUPS_START=datetime(2026, 9, 24, tzinfo=LISBON),
        NO_EXAM_SIGNUPS_END=datetime(2026, 10, 16, tzinfo=LISBON),
        NO_EXAM_REGISTRATION_END=datetime(2026, 10, 16, tzinfo=LISBON),
        NO_EXAM_PAYMENTS_START=datetime(2026, 10, 12, tzinfo=LISBON),
        NO_EXAM_PAYMENTS_END=datetime(2026, 10, 18, tzinfo=LISBON),
    ):
        for when, signup, registration, payment in [
            (datetime(2026, 9, 23, 23, 59, tzinfo=LISBON), False, False, False),
            (datetime(2026, 9, 24, tzinfo=LISBON), True, True, False),
            (datetime(2026, 10, 12, tzinfo=LISBON), True, True, True),
            (datetime(2026, 10, 16, tzinfo=LISBON), False, False, True),
            (datetime(2026, 10, 18, tzinfo=LISBON), False, False, False),
        ]:
            with patch("portal.admissions.policy.timezone.now", return_value=when):
                assert new_signups_open() is signup
                assert registration_changes_open(student) is registration
                assert payment_window_open(student) is payment
        student.admissions_mode = "exam"
        assert payment_window_open(student)


def test_instructor_signup_cannot_bypass_closed_registration(client):
    with override_config(ACCOUNT_ALLOW_REGISTRATION=False):
        response = client.post(
            reverse("instructors_signup"), {"email": "bypass@example.com"}
        )
        assert response.status_code == 200
        assert b"Sign Up Closed" in response.content


def test_exam_eligibility_uses_this_hackathons_specialization(
    student, hackathon1, slu1, specialization
):
    from portal.hackathons.services import can_participate

    student.can_attend_next = True
    assert not can_participate(student, hackathon1)
    Grade.objects.create(
        user=student, unit=slu1, score=16, status="graded", on_time=True
    )
    student.can_attend_next = False
    assert can_participate(student, hackathon1)


def test_edition_preview_and_apply(instructor):
    from io import StringIO

    from django.core.management import call_command

    from portal.academy.management.commands.configure_edition import SPECIALIZATIONS
    from portal.academy.models import Specialization, Unit

    out = StringIO()
    call_command("configure_edition", hackathon_2_date="2026-12-20", stdout=out)
    assert "Preview only" in out.getvalue()
    assert not Unit.objects.exists()
    for i, (code, (start, end)) in enumerate(SPECIALIZATIONS.items(), 1):
        spec = Specialization.objects.create(code=code)
        codes = (
            [f"SLU{x:02}" for x in range(1, 20)] + ["SLU32", "SLU64"]
            if i == 1
            else [f"BLU{x:02}" for x in range((i - 2) * 3 + 1, (i - 1) * 3 + 1)]
        )
        for unit_code in codes:
            Unit.objects.create(
                code=unit_code, specialization=spec, instructor=instructor
            )
        Hackathon.objects.create(code=f"HCKT{i:02}", descending=False)
    call_command(
        "configure_edition", hackathon_2_date="2026-12-20", apply=True, stdout=out
    )
    assert (
        Unit.objects.filter(
            specialization_id="S01", required_for_certificate=True
        ).count()
        == 17
    )
    assert Unit.objects.get(pk="SLU01").due_date == date(2026, 11, 21)
    assert Unit.objects.get(pk="BLU15").due_date == date(2027, 4, 24)
    assert config.ADMISSIONS_MODE == "no_exam"
    assert config.NO_EXAM_USE_SCHEDULE
    assert config.NO_EXAM_REGISTRATION_END.astimezone(LISBON) == datetime(
        2026, 10, 16, tzinfo=LISBON
    )
    assert Hackathon.objects.get(pk="HCKT02").due_date == date(2026, 12, 20)
    assert config.NO_EXAM_PAYMENTS_END.astimezone(LISBON) == datetime(
        2026, 10, 18, tzinfo=LISBON
    )


def test_edition_refuses_activity_without_mutations(student, slu1):
    from io import StringIO

    from django.core.management import CommandError, call_command

    slu1.refresh_from_db()
    before = slu1.due_date
    Grade.objects.create(user=student, unit=slu1)
    with pytest.raises(CommandError, match="Historical course activity"):
        call_command(
            "configure_edition",
            hackathon_2_date="2026-12-20",
            apply=True,
            stdout=StringIO(),
        )
    slu1.refresh_from_db()
    expected = before.date() if isinstance(before, datetime) else before
    assert slu1.due_date == expected


def test_hackathon_transition_initializes_attendance_and_keeps_no_exam_access(
    client, instructor, student, hackathon1, grade_slu1
):
    student.admissions_mode = "no_exam"
    student.can_graduate = False
    student.save()
    client.force_login(instructor)
    url = reverse("hackathons:instructor-hackathon-admin", args=[hackathon1.pk])
    assert client.post(url, {"status": "bogus"}).status_code == 302
    hackathon1.refresh_from_db()
    assert hackathon1.status == "closed"
    assert client.post(url, {"status": "marking_presences"}).status_code == 302
    assert Attendance.objects.filter(user=student, hackathon=hackathon1).exists()
    assert (
        client.post(
            url, {"status": "generating_teams", student.username: "on"}
        ).status_code
        == 302
    )
    assert client.post(url, {"status": "generating_teams"}).status_code == 302
    assert hackathon1.teams.get().users.filter(pk=student.pk).exists()
    assert client.post(url, {"status": "ready"}).status_code == 302
    assert client.post(url, {"status": "submissions_open"}).status_code == 302
    hackathon1.refresh_from_db()
    assert hackathon1.status == "ready"  # Scoring files are required.


def test_invalid_schedule_fails_closed(student):
    student.admissions_mode = "no_exam"
    with override_config(
        ADMISSIONS_MODE="no_exam",
        ACCOUNT_ALLOW_REGISTRATION=True,
        NO_EXAM_REGISTRATION_OPEN=True,
        NO_EXAM_USE_SCHEDULE=True,
        NO_EXAM_SIGNUPS_START=datetime(2026, 10, 10, tzinfo=LISBON),
        NO_EXAM_SIGNUPS_END=datetime(2026, 10, 1, tzinfo=LISBON),
    ):
        assert not new_signups_open()
        assert not registration_changes_open(student)
        assert not payment_window_open(student)


def test_constance_form_rejects_invalid_calendar(request_factory):
    from constance.utils import get_values

    from portal.admissions.forms import AdmissionsConfigForm

    initial = get_values()
    form = AdmissionsConfigForm(initial=initial, request=None)
    data = {}
    for key in form.fields:
        value = form[key].value()
        if isinstance(value, datetime):
            data[key + "_0"] = value.strftime("%Y-%m-%d")
            data[key + "_1"] = value.strftime("%H:%M:%S")
        else:
            data[key] = value
    data.update(NO_EXAM_USE_SCHEDULE=True, ADMISSIONS_PAYMENT_DAYS=0)
    invalid = AdmissionsConfigForm(data=data, initial=initial, request=None)
    assert not invalid.is_valid()
    assert "ADMISSIONS_PAYMENT_DAYS" in invalid.errors


def test_s01_failure_and_h1_absence_block_later_course_but_not_s01(
    client, student, slu1, instructor, hackathon1
):
    from portal.academy.models import Specialization, Unit
    from portal.academy.services import progression_block_reason

    student.admissions_mode = "no_exam"
    student.save()
    spec2 = Specialization.objects.create(code="S02")
    unit2 = Unit.objects.create(
        code="BLU01",
        specialization=spec2,
        instructor=instructor,
        open=True,
        checksum="test",
    )
    client.force_login(student)
    grade = Grade.objects.create(
        user=student, unit=slu1, score=20, status="graded", on_time=False
    )
    with override_config(
        NO_EXAM_ACADEMY_ACCESS_OPEN=True,
        ACADEMY_START=datetime(2020, 1, 1, tzinfo=LISBON),
    ):
        assert progression_block_reason(student)
        assert (
            client.get(
                reverse("academy:student-unit-detail", args=[slu1.pk])
            ).status_code
            == 200
        )
        assert (
            client.get(
                reverse("academy:student-unit-detail", args=[unit2.pk])
            ).status_code
            == 404
        )
        assert (
            client.get(
                reverse("hackathons:student-hackathon-detail", args=[hackathon1.pk])
            ).status_code
            == 302
        )
        # The existing admin validation mechanism restores eligibility immediately.
        grade.on_time = True
        grade.save()
        assert not progression_block_reason(student)
        assert (
            client.get(
                reverse("academy:student-unit-detail", args=[unit2.pk])
            ).status_code
            == 200
        )
        hackathon1.status = "complete"
        hackathon1.save()
        assert progression_block_reason(student)
        assert (
            client.get(
                reverse("academy:student-unit-detail", args=[unit2.pk])
            ).status_code
            == 404
        )
        Attendance.objects.create(user=student, hackathon=hackathon1, present=True)
        assert not progression_block_reason(student)


def test_later_deadline_failure_only_affects_certificate(
    student, grade_slu1, instructor
):
    from portal.academy.models import Specialization, Unit
    from portal.academy.services import progression_block_reason

    student.admissions_mode = "no_exam"
    student.save()
    spec2 = Specialization.objects.create(code="S02")
    Unit.objects.create(
        code="BLU01",
        specialization=spec2,
        instructor=instructor,
        due_date=date(2020, 1, 1),
    )
    assert not check_graduation_status(student)
    assert not progression_block_reason(student)


@pytest.mark.parametrize("microseconds, expected", [(0, False), (-1, True)])
def test_submission_validity_uses_exact_recorded_deadline(
    client, student, slu1, microseconds, expected
):
    from datetime import timedelta

    slu1.due_date = date(2026, 10, 24)
    slu1.save()
    moment = unit_deadline(slu1) + timedelta(microseconds=microseconds)
    with patch("django.db.models.fields.timezone.now", return_value=moment):
        client.force_login(student)
        response = client.post(reverse("academy:student-unit-detail", args=[slu1.pk]))
    assert response.status_code == 302
    grade = Grade.objects.get()
    assert grade.created == moment
    assert grade.on_time is expected


def test_repeated_exam_result_notification_is_idempotent(student):
    from portal.applications.domain import ApplicationStatus, Domain
    from portal.applications.models import Application

    application = Application.objects.create(user=student)
    with patch.object(
        Domain, "get_application_status", return_value=ApplicationStatus.passed
    ):
        with patch(
            "portal.applications.domain.emails.send_application_is_over_passed"
        ) as send:
            assert Domain.application_over(application) == "passed"
            assert Domain.application_over(application) == "passed"
            assert send.call_count == 1
