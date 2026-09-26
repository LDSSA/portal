"""Exercise both workflows against the database and real candidate/staff endpoints."""
from datetime import timedelta
from importlib import import_module
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from constance import config
from constance.test import override_config
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils import timezone

from portal.admissions.policy import academy_open, new_signups_open
from portal.applications.models import Application, Challenge, Submission
from portal.hackathons.models import Attendance, Hackathon
from portal.selection.enrollment import (
    complete_registration,
    record_registration_step,
    reset_payment,
    review_payment,
    review_scholarship,
    submit_payment,
    upload_document,
)
from portal.selection.models import EnrollmentEmail, ScholarshipStatus, Selection
from portal.selection.notifications import deliver_pending_emails
from portal.selection.queries import SelectionQueries
from portal.selection.status import SelectionStatus as S
from portal.staff.domain import Events
from portal.users.forms import PortalSignupForm
from portal.users.models import AdmissionsMode, User

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def admissions_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.SECURE_SSL_REDIRECT = False
    now = timezone.now()
    with override_config(
        ADMISSIONS_MODE="exam",
        ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=True,
        NO_EXAM_REGISTRATION_OPEN=True,
        NO_EXAM_ACADEMY_ACCESS_OPEN=False,
        ACCOUNT_ALLOW_REGISTRATION=True,
        ADMISSIONS_ACCEPTING_PAYMENT_PROFS=True,
        ADMISSIONS_PAYMENT_DAYS=7,
        PORTAL_STATUS="admissions:applications",
        ADMISSIONS_APPLICATIONS_START=now - timedelta(days=1),
        ADMISSIONS_SELECTION_START=now + timedelta(days=5),
        ACADEMY_START=now + timedelta(days=10),
    ):
        yield


@pytest.fixture
def candidate_factory():
    def make(mode="no_exam", verified=True, **kwargs):
        key = uuid4().hex
        user = User.objects.create(
            username=key,
            email=f"{key}@example.com",
            name="Test Applicant",
            gender="other",
            ticket_type="regular",
            admissions_mode=mode,
            **kwargs,
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=verified, primary=True
        )
        return user

    return make


@pytest.fixture
def staff(candidate_factory):
    return candidate_factory(is_staff=True)


@pytest.fixture
def challenges():
    return [
        Challenge.objects.create(code=code, pass_score=16, max_score=20)
        for code in ("coding_test", "slu01", "slu02", "slu03")
    ]


def complete(user, scholarship=False):
    record_registration_step(user, "coc", True)
    record_registration_step(user, "scholarship", scholarship)
    record_registration_step(user, "academy_type", "remote_only")
    user.refresh_from_db()
    return Selection.objects.filter(user=user).first()


def proof(user, student=False):
    upload_document(
        user, SimpleUploadedFile("payment.pdf", b"payment-proof"), "payment_proof"
    )
    if student:
        upload_document(
            user, SimpleUploadedFile("student.pdf", b"student-id"), "student_id"
        )
    submit_payment(user)


def exam_selected(user):
    complete(user)
    selection = Selection.objects.create(user=user, status=S.SELECTED)
    from portal.selection.payment import load_payment_data

    load_payment_data(selection)
    return selection


def test_no_exam_registration_has_no_exam_dependencies(candidate_factory, client):
    user = candidate_factory()
    client.force_login(user)
    for route, data in (
        ("codeofconduct", {"accepted": "on"}),
        ("scholarship", {"decision": "no"}),
        ("academy_type", {"academy_type": "remote_only"}),
    ):
        assert client.get(reverse(f"admissions:candidate:{route}")).status_code == 200
        assert (
            client.post(reverse(f"admissions:candidate:{route}"), data).status_code
            == 302
        )
    user.refresh_from_db()
    selection = user.selection
    assert selection.status == S.SELECTED
    assert selection.payment_value == 500
    assert not user.is_student
    assert user.registration_completed_at is not None
    assert not Application.objects.exists()
    assert not Challenge.objects.exists()
    response = client.get(reverse("admissions:candidate:home"))
    assert response.status_code == 200
    assert "candidate_templates/home_no_exam.html" in [
        t.name for t in response.templates
    ]
    assert b"4. The admission tests" not in response.content
    assert client.get(reverse("admissions:candidate:payment")).status_code == 200
    assert EnrollmentEmail.objects.count() == 1


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_signup_captures_default_once(mode, candidate_factory):
    config.ADMISSIONS_MODE = mode
    user = candidate_factory(mode="exam")
    form = PortalSignupForm(
        {"name": "Name", "gender": "other", "ticket_type": "regular"}
    )
    assert form.is_valid()
    form.signup(None, user)
    config.ADMISSIONS_MODE = "exam" if mode == "no_exam" else "no_exam"
    user.refresh_from_db()
    assert user.admissions_mode == mode


def test_default_toggle_does_not_move_existing_exam_applicant(
    candidate_factory, challenges, client
):
    user = candidate_factory(mode="exam")
    config.ADMISSIONS_MODE = "no_exam"
    complete(user)
    assert Application.objects.filter(user=user).exists()
    assert not Selection.objects.filter(user=user).exists()
    client.force_login(user)
    response = client.get(reverse("admissions:candidate:home"))
    assert response.status_code == 200
    assert b"4. The admission tests" in response.content
    assert (
        client.get(reverse("admissions:candidate:before-coding-test")).status_code
        == 200
    )


@pytest.mark.parametrize(
    "route,args",
    [
        ("before-coding-test", []),
        ("confirmation-coding-test", []),
        ("coding-test", []),
        ("slu", ["slu01"]),
        ("assignment-download", ["slu01"]),
        ("submission-download", [123]),
        ("submissions-feedback-download", [123]),
        ("submission-upload", ["slu01"]),
    ],
)
def test_no_exam_cannot_access_exam_urls(route, args, candidate_factory, client):
    user = candidate_factory()
    client.force_login(user)
    url = reverse(f"admissions:candidate:{route}", args=args)
    assert client.get(url).status_code == 404
    assert client.post(url).status_code == 404
    assert not Application.objects.exists()
    assert not Submission.objects.exists()


def test_registration_completion_is_idempotent(candidate_factory):
    user = candidate_factory()
    first = complete(user)
    deadline = first.payment_due_date
    complete_registration(user)
    record_registration_step(user, "academy_type", "remote_only")
    first.refresh_from_db()
    assert Selection.objects.filter(user=user).count() == 1
    assert EnrollmentEmail.objects.count() == 1
    assert first.payment_due_date == deadline


def test_unverified_applicant_cannot_complete(candidate_factory, client):
    user = candidate_factory(verified=False)
    client.force_login(user)
    assert client.get(reverse("admissions:candidate:codeofconduct")).status_code == 302
    with pytest.raises(ValidationError):
        record_registration_step(user, "coc", True)
    assert complete_registration(user) is None
    assert not Selection.objects.exists()


def test_email_confirmation_completes_ready_registration(candidate_factory):
    user = candidate_factory(
        verified=False,
        code_of_conduct_accepted=True,
        applying_for_scholarship=False,
        academy_type_preference="remote_only",
    )
    address = user.emailaddress_set.get()
    address.verified = True
    address.save()
    email_confirmed.send(sender=EmailAddress, request=None, email_address=address)
    assert Selection.objects.get(user=user).status == S.SELECTED


@pytest.mark.parametrize(
    "step,value", [("coc", False), ("scholarship", "yes"), ("academy_type", "invalid")]
)
def test_invalid_registration_input_is_rejected(step, value, candidate_factory):
    user = candidate_factory()
    with pytest.raises(ValidationError):
        record_registration_step(user, step, value)
    assert not Selection.objects.exists()


def test_scholarship_choice_cannot_be_rewritten(candidate_factory, client):
    user = candidate_factory()
    complete(user, scholarship=True)
    client.force_login(user)
    client.post(reverse("admissions:candidate:scholarship"), {"decision": "no"})
    client.post(
        reverse("users:profile"),
        {"name": user.name, "gender": "other", "ticket_type": "regular"},
    )
    user.refresh_from_db()
    assert user.applying_for_scholarship
    assert user.ticket_type == "scholarship"
    assert user.selection.status == S.INTERVIEW


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_scholarship_refusal_ends_admission(mode, candidate_factory, staff):
    user = candidate_factory(mode=mode)
    selection = complete(user, scholarship=True)
    if mode == "exam":
        selection = Selection.objects.create(
            user=user, status=S.INTERVIEW, scholarship_status=ScholarshipStatus.PENDING
        )
    review_scholarship(user, staff, "reject", "Scholarship criteria not met.")
    user.refresh_from_db()
    selection.refresh_from_db()
    assert selection.status == S.REJECTED
    assert selection.scholarship_status == ScholarshipStatus.REJECTED
    assert selection.scholarship_decided_by == staff
    assert selection.payment_value is None
    assert user.ticket_type == "scholarship"
    assert not user.is_student
    with pytest.raises(ValidationError):
        submit_payment(user)
    with pytest.raises(ValidationError):
        review_payment(user, staff, "accept")
    with pytest.raises(ValidationError):
        reset_payment(user, staff, "Change category", "regular")
    assert complete_registration(user).status == S.REJECTED


def test_scholarship_approval_then_payment(candidate_factory, staff):
    user = candidate_factory()
    selection = complete(user, scholarship=True)
    assert selection.payment_value is None
    with pytest.raises(ValidationError):
        proof(user)
    review_scholarship(user, staff, "accept")
    selection.refresh_from_db()
    assert selection.payment_value == 20
    assert selection.scholarship_status == ScholarshipStatus.APPROVED
    assert selection.status == S.SELECTED
    proof(user)
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    assert user.is_student


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_payment_activates_only_no_exam_mode(mode, candidate_factory, staff):
    user = candidate_factory(mode=mode)
    if mode == "exam":
        exam_selected(user)
    else:
        complete(user)
    # Changing the default must not change the saved applicant's activation rule.
    config.ADMISSIONS_MODE = "no_exam" if mode == "exam" else "exam"
    hackathon = Hackathon.objects.create(code="test", descending=False)
    proof(user)
    review_payment(user, staff, "accept")
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    assert user.selection.status == S.ACCEPTED
    assert user.is_student == (mode == "no_exam")
    assert Attendance.objects.filter(user=user, hackathon=hackathon).count() == (
        1 if mode == "no_exam" else 0
    )
    assert (
        EnrollmentEmail.objects.filter(
            event_key=f"{user.selection.pk}:payment-accepted"
        ).count()
        == 1
    )


def test_student_ticket_requires_student_id(candidate_factory, staff):
    user = candidate_factory()
    user.ticket_type = "student"
    user.save()
    complete(user)
    upload_document(user, SimpleUploadedFile("proof.pdf", b"proof"), "payment_proof")
    with pytest.raises(ValidationError):
        submit_payment(user)
    upload_document(user, SimpleUploadedFile("id.pdf", b"id"), "student_id")
    submit_payment(user)
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    assert user.is_student


def test_terminal_payment_cannot_be_reset_or_reopened(candidate_factory, staff):
    user = candidate_factory()
    complete(user)
    proof(user)
    review_payment(user, staff, "accept")
    with pytest.raises(ValidationError):
        reset_payment(user, staff, "reset")
    with pytest.raises(ValidationError):
        submit_payment(user)
    with pytest.raises(ValidationError):
        upload_document(user, SimpleUploadedFile("x", b"x"), "payment_proof")
    with pytest.raises(ValidationError):
        review_payment(user, staff, "reject", "late rejection")


def test_payment_upload_switch_does_not_prevent_staff_review(candidate_factory, staff):
    user = candidate_factory()
    complete(user)
    proof(user)
    config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS = False
    with pytest.raises(ValidationError):
        upload_document(user, SimpleUploadedFile("x", b"x"), "payment_proof")
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    assert user.is_student


def test_course_access_requires_payment_date_and_switch(
    candidate_factory, staff, client
):
    user = candidate_factory(github_username="test", slack_member_id="test")
    complete(user)
    proof(user)
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    client.force_login(user)
    url = reverse("academy:student-unit-list")
    assert client.get(url).status_code == 403
    config.NO_EXAM_ACADEMY_ACCESS_OPEN = True
    assert client.get(url).status_code == 403
    config.ACADEMY_START = timezone.now() - timedelta(days=1)
    assert academy_open(user)
    assert client.get(url).status_code == 200


def test_legacy_events_and_draw_ignore_no_exam(candidate_factory):
    waiting = candidate_factory()
    complete(waiting, scholarship=True)
    user = candidate_factory(mode="exam")
    selection = exam_selected(user)
    selection.status = S.ACCEPTED
    selection.save()
    config.PORTAL_STATUS = "admissions:selection"
    Events.trigger_admissions_are_over()
    user.refresh_from_db()
    waiting.refresh_from_db()
    assert user.is_student
    assert not waiting.is_student
    assert waiting.selection.status == S.INTERVIEW
    assert SelectionQueries.get_all().count() == 1
    assert SelectionQueries.get_all(mode=None).count() == 2


def test_application_end_ignores_stale_no_exam_application(candidate_factory):
    user = candidate_factory()
    Application.objects.create(user=user)
    config.PORTAL_STATUS = "admissions:selection"
    with patch("portal.staff.domain.ApplicationDomain.application_over") as finish:
        Events.trigger_applications_are_over()
    finish.assert_not_called()


def test_scheduler_does_not_close_no_exam_registration():
    config.ADMISSIONS_MODE = "no_exam"
    config.ADMISSIONS_SELECTION_START = timezone.now() - timedelta(days=1)
    import_module(
        "portal.scheduler.management.commands.run-scheduler"
    ).update_portal_status()
    assert config.ACCOUNT_ALLOW_REGISTRATION
    assert new_signups_open()
    config.ADMISSIONS_MODE = "exam"
    assert not new_signups_open()


def test_superuser_controls_default_and_regular_staff_cannot(candidate_factory, client):
    url = reverse("admissions:staff:home")
    staff = candidate_factory(is_staff=True)
    client.force_login(staff)
    assert client.get(url).status_code == 200
    assert (
        client.post(
            url, {"key": "admissions_mode", "admissions_mode": "no_exam"}
        ).status_code
        == 403
    )
    assert config.ADMISSIONS_MODE == "exam"
    staff.is_superuser = True
    staff.save()
    assert (
        client.post(
            url, {"key": "admissions_mode", "admissions_mode": "invalid"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            url, {"key": "admissions_mode", "admissions_mode": "no_exam"}
        ).status_code
        == 302
    )
    assert config.ADMISSIONS_MODE == "no_exam"


def test_shared_staff_pages_work_during_academy(candidate_factory, staff, client):
    user = candidate_factory()
    complete(user, scholarship=True)
    payer = candidate_factory()
    complete(payer)
    config.PORTAL_STATUS = "academy"
    client.force_login(staff)
    for route, args in [
        ("home", []),
        ("candidate-list", []),
        ("candidate-detail", [user.pk]),
        ("interview-list", []),
        ("interview-detail", [user.pk]),
        ("payment-list", []),
        ("payment-detail", [payer.pk]),
        ("export-candidates", []),
    ]:
        assert (
            client.get(reverse(f"admissions:staff:{route}", args=args)).status_code
            == 200
        )


def test_outbox_retries_without_repeating_registration(candidate_factory):
    user = candidate_factory()
    complete(user)
    with patch(
        "portal.selection.notifications.EmailMessage.send",
        side_effect=RuntimeError("offline"),
    ):
        assert deliver_pending_emails() == 0
    item = EnrollmentEmail.objects.get()
    assert item.attempts == 1 and item.sent_at is None
    assert item.next_attempt_at > timezone.now()
    complete_registration(user)
    assert EnrollmentEmail.objects.count() == 1
    item.next_attempt_at = timezone.now()
    item.save()
    assert deliver_pending_emails() == 1
    assert deliver_pending_emails() == 0
    assert len(mail.outbox) == 1


def test_pristine_conversion_is_explicit_and_active_conversion_refused(
    candidate_factory,
):
    user = candidate_factory(mode="exam")
    Application.objects.create(user=user)  # Legacy home GET may have created this.
    args = ["set-admissions-mode", "--user", user.email, "--mode", "no_exam"]
    call_command(*args, stdout=StringIO())
    user.refresh_from_db()
    assert user.admissions_requires_exam
    call_command(*args, "--apply", stdout=StringIO())
    user.refresh_from_db()
    assert not user.admissions_requires_exam
    record_registration_step(user, "coc", True)
    with pytest.raises(CommandError):
        call_command(*args, "--apply", stdout=StringIO())


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_real_signup_requires_email_confirmation(mode, client):
    config.ADMISSIONS_MODE = mode
    response = client.post(
        reverse("account_signup"),
        {
            "email": f"new-applicant-{mode}@example.com",
            "name": "New Applicant",
            "gender": "other",
            "ticket_type": "regular",
            "password1": "Strong-Example-Password-134!",
            "password2": "Strong-Example-Password-134!",
        },
    )
    assert response.status_code == 302
    user = User.objects.get(email=f"new-applicant-{mode}@example.com")
    assert user.admissions_mode == mode
    assert not user.emailaddress_set.get().verified
    assert not Selection.objects.filter(user=user).exists()
    assert not user.is_student
    assert len(mail.outbox) == 1
    assert mail.outbox[0].template_id == "Admissions - generic message"
    assert "confirm-email" in mail.outbox[0].body
    assert "August" not in mail.outbox[0].body


@pytest.mark.parametrize("route", ["codeofconduct", "scholarship", "academy_type"])
def test_anonymous_registration_requires_login(route, client):
    response = client.get(reverse(f"admissions:candidate:{route}"))
    assert response.status_code == 302
    assert reverse("account_login") in response.url


def test_registration_closed_does_not_block_existing_payment(candidate_factory, client):
    user = candidate_factory()
    complete(user)
    config.NO_EXAM_REGISTRATION_OPEN = False
    config.PORTAL_STATUS = "academy"
    config.ADMISSIONS_MODE = "no_exam"
    assert not new_signups_open()
    client.force_login(user)
    assert client.get(reverse("admissions:candidate:home")).status_code == 200
    assert client.get(reverse("admissions:candidate:payment")).status_code == 200
    proof(user)
    fresh = candidate_factory()
    with pytest.raises(ValidationError):
        record_registration_step(fresh, "coc", True)


def test_profile_completion_finishes_registration(candidate_factory, client):
    user = candidate_factory(
        code_of_conduct_accepted=True,
        applying_for_scholarship=False,
        academy_type_preference="remote_only",
    )
    user.name = ""
    user.save()
    assert complete_registration(user) is None
    client.force_login(user)
    response = client.post(
        reverse("users:profile"),
        {
            "name": "Completed Name",
            "gender": "other",
            "ticket_type": "regular",
        },
    )
    assert response.status_code == 302
    assert Selection.objects.get(user=user).status == S.SELECTED


def test_documents_are_private(candidate_factory, staff, client):
    owner = candidate_factory()
    complete(owner)
    proof(owner)
    doc = owner.selection.documents.get()
    url = reverse("admissions:candidate:payment-document-download", args=[doc.pk])
    stranger = candidate_factory()
    client.force_login(stranger)
    assert client.get(url).status_code == 404
    client.force_login(owner)
    response = client.get(url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"payment-proof"
    client.force_login(staff)
    response = client.get(url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"payment-proof"


def test_staff_payment_posts_and_additional_document_cycle(
    candidate_factory, staff, client
):
    user = candidate_factory()
    complete(user)
    candidate_url = reverse("admissions:candidate:payment")
    review_url = reverse("admissions:staff:payment-detail", args=[user.pk])
    client.force_login(user)
    # No proof: cannot silently advance into staff review.
    assert client.post(candidate_url).status_code == 302
    assert Selection.objects.get(user=user).status == S.SELECTED
    assert (
        client.post(
            reverse("admissions:candidate:payment-proof-upload"),
            {
                "file": SimpleUploadedFile("proof.pdf", b"proof"),
            },
        ).status_code
        == 302
    )
    client.post(candidate_url)
    client.force_login(staff)
    response = client.get(review_url)
    assert response.status_code == 200
    assert b"Accept existing proof" in response.content
    client.post(
        review_url,
        {"action": "ask_additional", "msg": "Please provide the complete receipt."},
    )
    assert Selection.objects.get(user=user).status == S.SELECTED
    client.force_login(user)
    client.post(
        reverse("admissions:candidate:payment-proof-upload"),
        {
            "file": SimpleUploadedFile("proof2.pdf", b"complete proof"),
        },
    )
    client.post(candidate_url)
    client.force_login(staff)
    client.post(review_url, {"action": "accept"})
    user.refresh_from_db()
    assert user.is_student


def test_payment_reset_is_explicit_and_updates_frozen_ticket(candidate_factory, staff):
    user = candidate_factory()
    first = complete(user)
    old_deadline = first.payment_due_date
    reset_payment(user, staff, "Correct category to company", "company")
    first.refresh_from_db()
    assert first.payment_value == 1500
    assert first.ticket_type == "company"
    assert first.payment_due_date > old_deadline
    assert first.status == S.SELECTED
    assert EnrollmentEmail.objects.filter(selection=first).count() == 2


def test_exam_pipeline_can_finish_after_default_switch(
    candidate_factory, staff, challenges, client
):
    from portal.applications.domain import Domain as ApplicationDomain
    from portal.selection.domain import SelectionDomain
    from portal.selection.select import select

    user = candidate_factory(mode="exam")
    complete(user)
    config.ADMISSIONS_MODE = "no_exam"
    client.force_login(user)
    response = client.post(reverse("admissions:candidate:confirmation-coding-test"))
    assert response.status_code == 302
    application = Application.objects.get(user=user)
    assert application.coding_test_started_at is not None
    for challenge in challenges:
        assert ApplicationDomain.can_add_submission(application, challenge)
        with patch("portal.candidate.views.import_string") as grader_class:
            response = client.post(
                reverse("admissions:candidate:submission-upload", args=[challenge.pk]),
                {
                    "file": SimpleUploadedFile("exercise.ipynb", b'{"cells": []}'),
                },
            )
        assert response.status_code == 302
        grader_class.return_value.return_value.run_grading.assert_called_once()
        Submission.objects.filter(application=application, unit=challenge).update(
            score=20, status="graded"
        )
    config.PORTAL_STATUS = "admissions:selection"
    Events.trigger_applications_are_over()
    selection = Selection.objects.get(user=user)
    assert selection.status == S.PASSED_TEST
    SelectionDomain.update_status(selection, S.DRAWN)
    select()
    selection.refresh_from_db()
    assert selection.status == S.SELECTED
    proof(user)
    review_payment(user, staff, "accept")
    user.refresh_from_db()
    assert not user.is_student
    Events.trigger_admissions_are_over()
    user.refresh_from_db()
    assert user.is_student


def test_grading_accepts_saved_exam_only(candidate_factory, staff, challenges):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(staff)
    config.ADMISSIONS_MODE = "no_exam"
    for mode in AdmissionsMode.values:
        user = candidate_factory(mode=mode)
        application = Application.objects.create(user=user)
        sub = Submission.objects.create(
            user=user, application=application, unit=challenges[0]
        )
        response = client.patch(
            reverse("grading:admissions-grade", args=[sub.pk]),
            {"score": 20, "status": "graded"},
        )
        assert response.status_code == (200 if mode == "exam" else 404)
        sub.refresh_from_db()
        assert sub.score == (20 if mode == "exam" else 0)


@pytest.mark.django_db(transaction=True)
def test_concurrent_completion_and_payment_are_idempotent(candidate_factory, staff):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    user = candidate_factory(
        code_of_conduct_accepted=True,
        applying_for_scholarship=False,
        academy_type_preference="remote_only",
    )
    barrier = Barrier(2)

    def concurrently(operation):
        def invoke(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                operation()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(invoke, range(2)))

    concurrently(lambda: complete_registration(user))
    assert Selection.objects.filter(user=user).count() == 1
    assert EnrollmentEmail.objects.count() == 1
    Hackathon.objects.create(code="concurrency", descending=False)
    proof(user)
    concurrently(lambda: review_payment(user, staff, "accept"))
    user.refresh_from_db()
    assert user.is_student
    assert Attendance.objects.filter(user=user).count() == 1
    assert (
        EnrollmentEmail.objects.filter(
            event_key=f"{user.selection.pk}:payment-accepted"
        ).count()
        == 1
    )


def test_enrollment_email_uses_existing_elastic_template(candidate_factory, settings):
    import json

    from django.core.mail import get_connection

    user = candidate_factory()
    complete(user)
    deliver_pending_emails()
    message = mail.outbox[0]
    settings.ANYMAIL = {"ELASTICMAIL_API_KEY": "test-only-no-network"}
    backend = get_connection(
        "portal.anymail_elasticmail.elasticmail.ElasticmailBackend"
    )
    payload = backend.build_message_payload(message, defaults={})
    data = json.loads(payload.serialize_data())
    assert data["Content"]["TemplateName"] == "Admissions - generic message"
    assert "500" in data["Content"]["Merge"]["message"]
    assert data["Recipients"]["To"] == [user.email]


def test_staff_cannot_read_stale_no_exam_submission(
    candidate_factory, staff, challenges, client
):
    user = candidate_factory()
    application = Application.objects.create(user=user)
    submission = Submission.objects.create(
        user=user, application=application, unit=challenges[0]
    )
    client.force_login(staff)
    assert (
        client.get(
            reverse("admissions:candidate:submission-download", args=[submission.pk])
        ).status_code
        == 404
    )
    assert (
        client.get(
            reverse("admissions:staff:submission-download", args=[submission.pk])
        ).status_code
        == 404
    )


@pytest.mark.parametrize("mode", AdmissionsMode.values)
@pytest.mark.parametrize("enabled", [True, False])
def test_attendance_toggle_controls_steps_and_registration(
    mode, enabled, candidate_factory, client, challenges
):
    from portal.admissions.policy import registration_ready

    user = candidate_factory(mode=mode)
    client.force_login(user)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=enabled):
        client.post(reverse("admissions:candidate:codeofconduct"), {"accepted": "on"})
        client.post(reverse("admissions:candidate:scholarship"), {"decision": "no"})
        user.refresh_from_db()
        assert not user.academy_type_preference
        assert registration_ready(user) is not enabled
        assert (user.registration_completed_at is not None) is not enabled
        home = client.get(reverse("admissions:candidate:home"))
        body = home.content.decode()
        assert ("3. Choose your preference" in body) is enabled
        if mode == "exam":
            assert f"{4 if enabled else 3}. The admission tests" in body
            response = client.post(
                reverse("admissions:candidate:confirmation-coding-test")
            )
            assert response.status_code == 302
            assert (
                Application.objects.get(user=user).coding_test_started_at is not None
            ) is not enabled
        else:
            assert "The admission tests" not in body
            assert Selection.objects.filter(user=user).exists() is not enabled


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_disabled_attendance_blocks_direct_writes_and_preserves_answer(
    mode, candidate_factory, client
):
    user = candidate_factory(
        mode=mode,
        code_of_conduct_accepted=True,
        applying_for_scholarship=False,
        academy_type_preference="remote_only",
    )
    client.force_login(user)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False):
        url = reverse("admissions:candidate:academy_type")
        for response in (
            client.get(url),
            client.post(url, {"academy_type": "in_person_only"}),
        ):
            assert response.status_code == 302
            assert response.url == reverse("admissions:candidate:home")
        with pytest.raises(ValidationError, match="survey is disabled"):
            record_registration_step(user, "academy_type", "in_person_only")
    user.refresh_from_db()
    assert user.academy_type_preference == "remote_only"


@pytest.mark.parametrize("scholarship", [False, True])
def test_disabling_survey_unblocks_existing_registration_once(
    scholarship, candidate_factory, client
):
    user = candidate_factory()
    record_registration_step(user, "coc", True)
    record_registration_step(user, "scholarship", scholarship)
    assert not Selection.objects.filter(user=user).exists()
    client.force_login(user)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False):
        body = client.get(reverse("admissions:candidate:home")).content.decode()
        assert "Complete registration</button>" in body
        for _ in range(2):
            response = client.post(
                reverse("admissions:candidate:complete-registration")
            )
            assert response.status_code == 302
        selection = Selection.objects.get(user=user)
        assert selection.status == (S.INTERVIEW if scholarship else S.SELECTED)
        assert EnrollmentEmail.objects.filter(selection=selection).count() == 1
    user.refresh_from_db()
    assert not user.academy_type_preference


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_reenabling_survey_preserves_completed_registration(
    mode, candidate_factory, client, staff, challenges
):
    from portal.admissions.policy import registration_ready

    user = candidate_factory(mode=mode)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False):
        record_registration_step(user, "coc", True)
        record_registration_step(user, "scholarship", False)
    user.refresh_from_db()
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=True):
        assert registration_ready(user)
        client.force_login(user)
        body = client.get(reverse("admissions:candidate:home")).content.decode()
        assert "3. Choose your preference" not in body
        if mode == "exam":
            client.post(reverse("admissions:candidate:confirmation-coding-test"))
            assert Application.objects.get(user=user).coding_test_started_at is not None
        else:
            proof(user)
            review_payment(user, staff, "accept")
            user.refresh_from_db()
            assert user.is_student
        assert not user.academy_type_preference


@pytest.mark.parametrize("mode", AdmissionsMode.values)
def test_reenabled_survey_still_required_for_unfinished_applicant(
    mode, candidate_factory
):
    from portal.admissions.policy import registration_ready

    user = candidate_factory(
        mode=mode, code_of_conduct_accepted=True, applying_for_scholarship=False
    )
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False):
        assert registration_ready(user)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=True):
        assert not registration_ready(user)
        record_registration_step(user, "academy_type", "remote_only")
        user.refresh_from_db()
        assert registration_ready(user)


def test_survey_bypass_does_not_bypass_registration_closure(candidate_factory):
    user = candidate_factory(
        code_of_conduct_accepted=True, applying_for_scholarship=False
    )
    with override_config(
        ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False, NO_EXAM_REGISTRATION_OPEN=False
    ):
        assert complete_registration(user) is None
        assert not Selection.objects.filter(user=user).exists()


def test_existing_exam_applicant_completes_when_survey_is_disabled(
    candidate_factory, client, challenges
):
    user = candidate_factory(mode="exam")
    record_registration_step(user, "coc", True)
    record_registration_step(user, "scholarship", False)
    user.refresh_from_db()
    assert user.registration_completed_at is None
    client.force_login(user)
    client.get(reverse("admissions:candidate:home"))
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=False):
        response = client.post(reverse("admissions:candidate:confirmation-coding-test"))
        assert response.status_code == 302
    user.refresh_from_db()
    assert user.registration_completed_at is not None
    assert not user.academy_type_preference
    assert Application.objects.get(user=user).coding_test_started_at is not None
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=True):
        response = client.get(reverse("admissions:candidate:coding-test"))
        assert response.status_code == 200


def test_legacy_selected_applicant_does_not_need_survey(candidate_factory):
    from portal.admissions.policy import registration_ready

    user = candidate_factory(
        mode="exam", code_of_conduct_accepted=True, applying_for_scholarship=False
    )
    Selection.objects.create(user=user, status=S.SELECTED)
    with override_config(ADMISSIONS_ASK_ATTENDANCE_PREFERENCE=True):
        assert registration_ready(user)
        user.code_of_conduct_accepted = False
        assert not registration_ready(user)
