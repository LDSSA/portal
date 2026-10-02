from unittest.mock import patch

import pytest
from constance import config
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from portal.academy.models import Grade, Specialization, Unit
from portal.applications.models import (
    Application,
    Challenge,
)
from portal.applications.models import (
    Submission as ExamSubmission,
)
from portal.capstone.models import (
    Capstone,
    Datapoint,
    DueDatapoint,
    Report,
    Simulator,
    StudentApi,
)
from portal.edition_management import backups
from portal.edition_management.executor import process
from portal.edition_management.maintenance import (
    MaintenanceBusy,
    operation,
    state,
)
from portal.edition_management.models import EditionRun, GradingJob
from portal.edition_management.planner import create_preview, validate_jobs
from portal.edition_management.policy import CLEAR, model
from portal.hackathons.models import Attendance, Hackathon, Submission, Team
from portal.selection.models import (
    EnrollmentEmail,
    Selection,
    SelectionDocument,
    SelectionLogs,
)
from portal.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def operator(settings, tmp_path):
    settings.EDITION_BACKUP_DIR = str(tmp_path / "dumps")
    current = state()
    current.phase = "open"
    current.ready_release = settings.EDITION_RELEASE
    current.worker_release = settings.EDITION_RELEASE
    current.worker_seen = timezone.now()
    current.save()
    return User.objects.create_user(
        username="operator",
        email="operator@example.com",
        password="test",
        is_staff=True,
        is_superuser=True,
    )


def preview(operator, retained=()):
    current = state()
    current.phase = "maintenance"
    current.save()
    run = create_preview(operator, retained)
    run.status = "queued"
    run.backup_first = False
    run.save()
    return run


def activity(student):
    spec = Specialization.objects.create(code="S01", name="Bootcamp")
    unit = Unit.objects.create(
        code="SLU01",
        specialization=spec,
        instructor=student,
        open=True,
        checksum="real-checksum",
    )
    Grade.objects.create(user=student, unit=unit, status="graded")
    h = Hackathon.objects.create(code="HCKT01", descending=False, status="complete")
    team = Team.objects.create(hackathon=h)
    team.users.add(student)
    Attendance.objects.create(hackathon=h, user=student)
    Submission.objects.create(hackathon=h, content_object=team)
    Submission.objects.create(hackathon=h, content_object=student)
    cap = Capstone.objects.create(name="Capstone", proposal_open=True)
    simulator = Simulator.objects.create(
        capstone=cap, name="old run", ends=timezone.now(), status="started"
    )
    point = Datapoint.objects.create(simulator=simulator, data='{"input": 1}')
    DueDatapoint.objects.create(
        simulator=simulator,
        datapoint=point,
        user=student,
        url="https://example.invalid/predict",
        due=timezone.now(),
    )
    Report.objects.create(capstone=cap, user=student, type="proposal")
    StudentApi.objects.create(capstone=cap, user=student, url="https://example.invalid")
    app = Application.objects.create(user=student)
    challenge = Challenge.objects.create(code="coding_test")
    ExamSubmission.objects.create(
        application=app, user=student, unit=challenge, status="graded", score=18
    )
    selection = Selection.objects.create(user=student)
    SelectionDocument.objects.create(selection=selection, doc_type="payment_proof")
    SelectionLogs.objects.create(selection=selection, event="test", message="old")
    EnrollmentEmail.objects.create(
        selection=selection,
        event_key="old",
        recipient="old@example.com",
        subject="old",
        body="old",
    )
    return unit, cap, h


@pytest.mark.parametrize("mode", ["exam", "no_exam"])
def test_complete_reset_removes_both_simulator_point_models_and_exam_activity(
    operator, student, mode
):
    config.ADMISSIONS_MODE = mode
    unit, cap, h = activity(student)
    kept = Token.objects.create(user=operator)
    deleted_token = Token.objects.create(user=student).key
    old_date = unit.due_date
    run = preview(operator)
    process(run)
    run.refresh_from_db()
    assert run.status == "succeeded", run.error
    assert state().phase == "prepared"
    for label in CLEAR:
        assert not model(label).objects.exists(), label
    assert not User.objects.filter(pk=student.pk).exists()
    assert not Token.objects.filter(key=deleted_token).exists()
    assert Token.objects.get(user=operator).key == kept.key
    unit.refresh_from_db()
    cap.refresh_from_db()
    h.refresh_from_db()
    assert unit.instructor_id is None and not unit.open
    assert unit.checksum == "real-checksum" and unit.due_date == old_date
    assert not cap.proposal_open and h.status == "closed"
    assert config.ADMISSIONS_MODE == mode
    assert not config.ACCOUNT_ALLOW_REGISTRATION
    # Duplicate execution does not start another reset.
    process(run)
    assert state().generation == 1


def test_user_deletion_keeps_other_students_grades_and_team_submissions(
    operator, student
):
    unit, _, hackathon = activity(student)
    other_grade = Grade.objects.create(user=operator, unit=unit)
    token = Token.objects.create(user=student)
    team = Team.objects.get(hackathon=hackathon)
    student.delete()
    unit.refresh_from_db()
    assert unit.instructor_id is None
    assert Grade.objects.filter(pk=other_grade.pk).exists()
    assert not Token.objects.filter(pk=token.pk).exists()
    assert Submission.objects.count() == 1
    assert Submission.objects.get().content_object == team
    Team.objects.filter(pk=team.pk).delete()
    assert not Submission.objects.exists()


def test_optional_instructor_create_and_clear(operator):
    spec = Specialization.objects.create(code="S01")
    unit = Unit.objects.create(code="SLU01", specialization=spec)
    assert unit.instructor is None
    unit.instructor = operator
    unit.save()
    unit.instructor = None
    unit.save()
    assert Unit.objects.get(pk=unit.pk).instructor is None


def test_stale_preview_is_rejected(operator, student):
    activity(student)
    run = preview(operator)
    Unit.objects.update(name="edited after preview")
    process(run)
    run.refresh_from_db()
    assert run.status == "failed" and "changed" in run.error
    assert Grade.objects.exists() and Datapoint.objects.exists()
    assert state().phase == "maintenance"


def test_failure_rolls_back_every_deletion(operator, student):
    unit, _, _ = activity(student)
    run = preview(operator)
    with patch(
        "portal.edition_management.executor.close_public_access",
        side_effect=RuntimeError("injected"),
    ):
        process(run)
    run.refresh_from_db()
    unit.refresh_from_db()
    assert run.status == "failed"
    assert unit.instructor_id == student.pk and unit.open
    assert Datapoint.objects.count() == 1 and DueDatapoint.objects.count() == 1
    assert Grade.objects.exists() and User.objects.filter(pk=student.pk).exists()
    assert state().generation == 0


def test_failed_backup_prevents_reset(operator, student):
    activity(student)
    run = preview(operator)
    run.backup_first = True
    run.save()
    with patch(
        "portal.edition_management.backups.dump",
        side_effect=ValidationError("backup failed"),
    ):
        process(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.error == "backup failed"
    assert DueDatapoint.objects.exists() and User.objects.filter(pk=student.pk).exists()


def test_credentials_of_deselected_organizer_are_deleted(operator):
    former = User.objects.create_user(
        username="former", email="former@example.com", is_staff=True
    )
    key = Token.objects.create(user=former).key
    run = preview(operator)
    process(run)
    run.refresh_from_db()
    assert run.status == "succeeded", run.error
    assert not User.objects.filter(pk=former.pk).exists()
    assert not Token.objects.filter(key=key).exists()


def test_service_account_and_mixed_role_organizer(operator, settings):
    service = User.objects.create_user(
        username=settings.GRADING_USERNAME, email="service@example.com", is_staff=True
    )
    mixed = User.objects.create_user(
        username="mixed", email="mixed@example.com", is_student=True, is_instructor=True
    )
    key = Token.objects.create(user=service).key
    run = preview(operator, [mixed.pk])
    process(run)
    mixed.refresh_from_db()
    service.refresh_from_db()
    assert not mixed.is_student and mixed.is_instructor
    assert service.is_staff and Token.objects.get(user=service).key == key


def test_api_and_staff_cannot_control_reset(client, operator, student):
    url = reverse("admin:edition_control")
    client.force_login(student)
    assert client.post(url, {"action": "maintenance"}).status_code in (302, 403)
    student.is_staff = True
    student.save()
    assert client.post(url, {"action": "maintenance"}).status_code == 403
    assert state().phase == "open"


def test_admin_preview_requires_review_and_confirmation(client, operator, student):
    client.force_login(operator)
    url = reverse("admin:edition_control")
    response = client.get(url)
    assert response.status_code == 200
    assert (
        b"capstone.DueDatapoint" in response.content
        and b"capstone.Datapoint" in response.content
    )
    assert b"purge-dialog" in response.content
    assert b"admin/css/edition_management.css" in response.content
    assert b'class="module aligned"' in response.content
    assert b'class="submit-row"' in response.content
    assert b'class="default"' in response.content
    client.post(url, {"action": "maintenance"})
    response = client.post(url, {"action": "preview"})
    assert response.status_code == 302
    run = EditionRun.objects.get(kind="reset")
    run_url = reverse("admin:edition_run", args=[run.pk])
    client.post(run_url, {})
    run.refresh_from_db()
    assert run.status == "draft"
    client.post(run_url, {"reviewed": "on", "confirmed": "on"})
    run.refresh_from_db()
    assert run.status == "queued"
    client.post(run_url, {"reviewed": "on", "confirmed": "on"})
    assert EditionRun.objects.filter(status="queued").count() == 1


def test_account_review_explains_retention_and_cancel_preserves_data(
    client, operator, student, settings
):
    service = User.objects.create_user(
        username=settings.EDITION_SERVICE_USERS[0],
        email="service@example.com",
        is_staff=True,
    )
    organizer = User.objects.create_user(
        username="organizer",
        email="organizer@example.com",
        is_instructor=True,
    )
    deselected_organizer = User.objects.create_user(
        username="former-organizer",
        email="former-organizer@example.com",
        is_staff=True,
    )
    completed = User.objects.create_user(
        username="new-applicant",
        email="incoming@example.com",
        admissions_mode="no_exam",
        registration_completed_at=timezone.now(),
    )
    incomplete = User.objects.create_user(
        username="unclassified",
        email="unclassified@example.com",
        admissions_mode="exam",
    )
    application = Application.objects.create(user=completed)
    original_user_ids = set(User.objects.values_list("pk", flat=True))
    client.force_login(operator)
    control_url = reverse("admin:edition_control")

    response = client.post(control_url, {"action": "maintenance"}, follow=True)
    assert response.status_code == 200
    assert b"Organizers to retain" in response.content
    assert b"Only staff, superusers and instructors" in response.content
    assert organizer.username.encode() in response.content
    assert completed.username.encode() not in response.content

    response = client.post(
        control_url, {"action": "preview", "retained": [organizer.pk]}
    )
    assert response.status_code == 302
    run = EditionRun.objects.get(kind="reset")
    retained = {
        account["username"]: account["reason"]
        for account in run.plan["retained_accounts"]
    }
    assert retained == {
        operator.username: "Current operator — automatically retained",
        service.username: "Service account — automatically retained",
        organizer.username: "Selected organizer",
    }
    deleted = {account["username"]: account for account in run.plan["deleted_accounts"]}
    assert deleted[student.username]["classification"] == "Previous student account"
    assert (
        deleted[deselected_organizer.username]["classification"]
        == "Deselected organizer"
    )
    assert deleted[completed.username]["registration_completed_at"]
    assert deleted[incomplete.username]["registration_completed_at"] is None
    assert deselected_organizer.username not in {
        account["username"] for account in run.plan["review_accounts"]
    }

    run_url = reverse("admin:edition_run", args=[run.pk])
    preview_response = client.get(run_url)
    assert b"Potential applicant or unclassified accounts" in preview_response.content
    assert b"cannot be retained by this reset" in preview_response.content
    assert b"Completed:" in preview_response.content
    assert b"Incomplete / not recorded" in preview_response.content
    assert b'name="retained"' not in preview_response.content
    assert (
        b"Cancel reset preparation and keep the current database"
        in preview_response.content
    )

    cancel_response = client.post(control_url, {"action": "cancel"})
    assert cancel_response.status_code == 302
    run.refresh_from_db()
    assert state().phase == "open" and run.status == "cancelled"
    assert set(User.objects.values_list("pk", flat=True)) == original_user_ids
    assert Application.objects.filter(pk=application.pk, user=completed).exists()


def test_historical_account_preview_without_structured_rows_still_renders(
    client, operator, settings
):
    run = EditionRun.objects.create(
        kind="reset",
        status="cancelled",
        actor=operator,
        actor_username=operator.username,
        database="historical",
        release=settings.EDITION_RELEASE,
        plan={
            "retained_names": [operator.username],
            "deleted_names": ["legacy-account"],
            "review": ["legacy-account"],
        },
    )
    client.force_login(operator)
    response = client.get(reverse("admin:edition_run", args=[run.pk]))
    assert response.status_code == 200
    assert b"legacy-account" in response.content
    assert b"historical preview without registration details" in response.content


def test_purge_requires_server_side_confirmation(client, operator):
    client.force_login(operator)
    client.post(reverse("admin:edition_control"), {"action": "purge"})
    assert not EditionRun.objects.filter(kind="purge").exists()


def test_maintenance_blocks_requests_workers_and_grading(operator, client):
    current = state()
    current.phase = "maintenance"
    current.save()
    assert client.get("/").status_code == 503
    with pytest.raises(MaintenanceBusy):
        with operation():
            pytest.fail("gate admitted operation")
    from portal.selection.notifications import deliver_pending_emails

    with pytest.raises(MaintenanceBusy):
        deliver_pending_emails()
    job = GradingJob.objects.create(name="still-running", backend="kubernetes")
    with pytest.raises(ValidationError):
        validate_jobs()
    job.status = "finished"
    job.save()
    validate_jobs()


def test_abandoned_grading_records_are_reported_and_removed(client, operator, student):
    activity(student)
    Grade.objects.update(status="sent")
    ExamSubmission.objects.update(status="grading")
    client.force_login(operator)

    response = client.post(
        reverse("admin:edition_control"),
        {"action": "maintenance"},
        follow=True,
    )
    assert response.status_code == 200
    assert state().phase == "maintenance"
    assert (
        b"Unfinished grading records with no active external grader" in response.content
    )

    response = client.post(reverse("admin:edition_control"), {"action": "preview"})
    assert response.status_code == 302
    run = EditionRun.objects.get(kind="reset")
    assert run.plan["unfinished_grading"] == {
        "total": 2,
        "rows": [
            {"model": "academy.Grade", "count": 1},
            {"model": "applications.Submission", "count": 1},
        ],
    }
    preview_response = client.get(reverse("admin:edition_run", args=[run.pk]))
    assert b"Unfinished grading records" in preview_response.content
    assert b"do not block maintenance" in preview_response.content

    run.status = "queued"
    run.backup_first = False
    run.save(update_fields=["status", "backup_first"])
    process(run)
    run.refresh_from_db()
    assert run.status == "succeeded", run.error
    assert (
        run.result["unfinished_grading_records_deleted"]
        == run.plan["unfinished_grading"]
    )
    assert not Grade.objects.exists() and not ExamSubmission.objects.exists()


def test_private_backup_names_and_purge_do_not_follow_symlinks(operator, tmp_path):
    directory = backups.directory()
    innocent = tmp_path / "keep.txt"
    innocent.write_text("keep")
    link = (
        directory
        / "portal-20261001T123456123456Z-00000000000000000000000000000000.dump"
    )
    link.symlink_to(innocent)
    (directory / "unrelated.txt").write_text("keep")
    run = EditionRun.objects.create(actor=operator, backup_name=link.name)
    with pytest.raises(ValidationError):
        backups.open_dump(run)
    assert backups.purge() == 0
    assert innocent.read_text() == "keep" and (directory / "unrelated.txt").exists()


def test_unknown_user_on_keep_list_rejected(operator, student):
    current = state()
    current.phase = "maintenance"
    current.save()
    with pytest.raises(ValidationError):
        create_preview(operator, [student.pk])


def test_csrf_blocks_destructive_actions(operator):
    from django.test import Client

    client = Client(enforce_csrf_checks=True)
    client.force_login(operator)
    assert (
        client.post(
            reverse("admin:edition_control"), {"action": "maintenance"}
        ).status_code
        == 403
    )
    assert state().phase == "open"


def test_worker_and_migration_readiness_block_confirmation(client, operator):
    client.force_login(operator)
    run = preview(operator)
    run.status = "draft"
    run.save()
    current = state()
    current.worker_seen = None
    current.save()
    client.post(
        reverse("admin:edition_run", args=[run.pk]),
        {"reviewed": "on", "confirmed": "on"},
    )
    run.refresh_from_db()
    assert run.status == "draft"


def test_external_grader_discovery_blocks_even_after_grade_callback(operator, settings):
    import json
    from types import SimpleNamespace

    settings.GRADING_CLASS = "portal.grading.services.AcademyKubernetesGrading"
    payload = {
        "items": [
            {
                "metadata": {"name": "old-slu01-job"},
                "spec": {"containers": [{"image": "ldssa/batch-slu01"}]},
                "status": {"phase": "Running"},
            }
        ]
    }
    with patch(
        "portal.edition_management.jobs.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode()),
    ):
        with pytest.raises(ValidationError):
            validate_jobs()
    assert GradingJob.objects.get(name="old-slu01-job").remote_seen


def test_grader_monitoring_failure_still_blocks_maintenance(operator, settings):
    from types import SimpleNamespace

    settings.GRADING_CLASS = "portal.grading.services.AcademyKubernetesGrading"
    with patch(
        "portal.edition_management.jobs.subprocess.run",
        return_value=SimpleNamespace(returncode=1, stdout=b""),
    ):
        with pytest.raises(
            ValidationError, match="Cannot verify external grading jobs"
        ):
            validate_jobs()


@pytest.mark.django_db(transaction=True)
def test_shared_operation_gate_prevents_reset_in_another_connection(operator):
    import psycopg2
    from django.db import connection

    from portal.edition_management.maintenance import GATE, lock

    db = connection.settings_dict
    remote = psycopg2.connect(
        dbname=db["NAME"],
        user=db["USER"],
        host=db["HOST"],
        port=db["PORT"],
        password=db["PASSWORD"],
    )
    try:
        with remote.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock_shared(%s)", [GATE])
        with pytest.raises(MaintenanceBusy):
            with lock(exclusive=True):
                pytest.fail("exclusive reset entered during an active operation")
    finally:
        remote.close()
    with lock(exclusive=True):
        pass


@pytest.mark.django_db(transaction=True)
def test_real_dump_download_and_restore(operator, settings, client):
    import os
    import subprocess
    import uuid

    import psycopg2
    from django.db import connection

    spec = Specialization.objects.create(code="S01", name="preserved")
    Unit.objects.create(code="SLU01", specialization=spec)
    run = EditionRun.objects.create(
        kind="backup",
        status="queued",
        actor=operator,
        actor_username=operator.username,
        database=__import__(
            "portal.edition_management.planner", fromlist=["database_identity"]
        ).database_identity(),
        release=settings.EDITION_RELEASE,
    )
    process(run)
    run.refresh_from_db()
    assert run.status == "succeeded", run.error
    assert run.backup_bytes > 0 and len(run.backup_sha256) == 64
    assert backups.NAME.fullmatch(run.backup_name)
    assert (backups.directory() / run.backup_name).stat().st_mode & 0o777 == 0o600
    client.force_login(operator)
    response = client.get(reverse("admin:edition_download", args=[run.pk]))
    assert response.status_code == 200
    response.close()
    db = connection.settings_dict
    env = os.environ.copy()
    env.update(
        PGHOST=db["HOST"],
        PGPORT=str(db["PORT"]),
        PGUSER=db["USER"],
        PGPASSWORD=db["PASSWORD"] or "",
    )
    restored = "portal_restore_" + uuid.uuid4().hex
    admin_conn = psycopg2.connect(
        dbname="postgres",
        host=db["HOST"],
        port=db["PORT"],
        user=db["USER"],
        password=db["PASSWORD"],
    )
    admin_conn.autocommit = True
    try:
        from psycopg2 import sql

        with admin_conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restored))
            )
        subprocess.run(
            [
                "pg_restore",
                "--exit-on-error",
                "--dbname",
                restored,
                str(backups.directory() / run.backup_name),
            ],
            env=env,
            check=True,
            capture_output=True,
        )
        restored_conn = psycopg2.connect(
            dbname=restored,
            host=db["HOST"],
            port=db["PORT"],
            user=db["USER"],
            password=db["PASSWORD"],
        )
        with restored_conn.cursor() as cursor:
            cursor.execute("SELECT code, instructor_id FROM academy_unit")
            assert cursor.fetchall() == [("SLU01", None)]
        restored_conn.close()
    finally:
        with admin_conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(restored))
            )
        admin_conn.close()
    assert backups.purge() == 1
    assert not (backups.directory() / run.backup_name).exists()


@pytest.mark.django_db(transaction=True)
def test_instructor_migration_preserves_existing_assignments_and_grades():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    before = [node for node in latest if node[0] != "academy"] + [
        ("academy", "0015_grade_deadline_override_at_and_more")
    ]
    try:
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        user = old.get_model("users", "User").objects.create(username="legacy-teacher")
        spec = old.get_model("academy", "Specialization").objects.create(code="S01")
        unit = old.get_model("academy", "Unit").objects.create(
            code="SLU01", specialization=spec, instructor=user, checksum="unchanged"
        )
        grade = old.get_model("academy", "Grade").objects.create(user=user, unit=unit)
        MigrationExecutor(connection).migrate(latest)
        saved = Unit.objects.get(pk=unit.pk)
        assert saved.instructor_id == user.pk and saved.checksum == "unchanged"
        assert Grade.objects.filter(pk=grade.pk).exists()
        assert User.objects.filter(pk=user.pk).exists()
    finally:
        MigrationExecutor(connection).migrate(latest)


def test_worker_restart_preserves_success_and_marks_interruption(operator):
    from django.core.management import call_command

    committed = EditionRun.objects.create(status="succeeded", kind="reset")
    interrupted = EditionRun.objects.create(status="running", kind="reset")
    call_command("run-edition-resets", once=True)
    committed.refresh_from_db()
    interrupted.refresh_from_db()
    assert committed.status == "succeeded"
    assert interrupted.status == "failed"
    assert state().worker_seen is not None


def test_preview_has_per_model_delete_and_keep_counts(operator, student):
    activity(student)
    run = preview(operator)
    counts = {row["model"]: row for row in run.plan["rows"]}
    assert counts["capstone.Datapoint"]["delete"] == 1
    assert counts["capstone.DueDatapoint"]["delete"] == 1
    assert counts["academy.Unit"]["delete"] == 0
    assert counts["academy.Unit"]["keep"] == 1
    assert counts["academy.Unit"]["configure"] == 1
    assert counts["users.User"]["keep"] == 1
    assert counts["users.User"]["delete"] == 1
