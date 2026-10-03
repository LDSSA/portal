import pytest
from django.contrib import admin
from django.db import IntegrityError, transaction

from portal.users.admin import UserAdmin
from portal.users.models import User

pytestmark = pytest.mark.django_db


# def test_user_get_absolute_url(user: settings.AUTH_USER_MODEL):
#     assert user.get_absolute_url() == f"/users/{user.username}/"


@pytest.mark.parametrize("role", ["is_instructor", "is_staff", "is_superuser"])
def test_student_reset_retention_tracks_role_changes(role):
    user = User.objects.create_user(
        username="role-change",
        email="role-change@example.com",
        is_student=True,
    )
    assert user.retain_student_account_on_next_edition_reset is False

    user.retain_student_account_on_next_edition_reset = True
    user.save(update_fields=["retain_student_account_on_next_edition_reset"])
    setattr(user, role, True)
    user.save(update_fields=[role])
    user.refresh_from_db()
    assert user.retain_student_account_on_next_edition_reset is None

    setattr(user, role, False)
    user.save(update_fields=[role])
    user.refresh_from_db()
    assert user.retain_student_account_on_next_edition_reset is False


def test_enrollment_initializes_student_reset_retention():
    from portal.selection.enrollment import _activate_student

    user = User.objects.create_user(
        username="newly-enrolled",
        email="newly-enrolled@example.com",
    )
    assert user.retain_student_account_on_next_edition_reset is None
    _activate_student(user)
    user.refresh_from_db()
    assert user.is_student
    assert user.retain_student_account_on_next_edition_reset is False


def test_database_rejects_invalid_student_reset_retention():
    student = User.objects.create_user(
        username="student-constraint",
        email="student-constraint@example.com",
        is_student=True,
    )
    organizer = User.objects.create_user(
        username="organizer-constraint",
        email="organizer-constraint@example.com",
        is_instructor=True,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=student.pk).update(
            retain_student_account_on_next_edition_reset=None
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=organizer.pk).update(
            retain_student_account_on_next_edition_reset=True
        )


def test_admin_only_edits_retention_for_student_only_accounts():
    student = User.objects.create_user(
        username="student-admin-field",
        email="student-admin-field@example.com",
        is_student=True,
    )
    mixed = User.objects.create_user(
        username="mixed-admin-field",
        email="mixed-admin-field@example.com",
        is_student=True,
        is_staff=True,
    )
    applicant = User.objects.create_user(
        username="applicant-admin-field",
        email="applicant-admin-field@example.com",
    )
    user_admin = UserAdmin(User, admin.site)
    field = "retain_student_account_on_next_edition_reset"

    assert field not in user_admin.get_readonly_fields(None, student)
    assert field in user_admin.get_readonly_fields(None, mixed)
    assert field in user_admin.get_readonly_fields(None, applicant)


@pytest.mark.django_db(transaction=True)
def test_student_reset_retention_data_migration():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    before = [node for node in latest if node[0] != "users"] + [
        ("users", "0023_user_admissions_mode_user_registration_completed_at")
    ]
    try:
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        OldUser = old.get_model("users", "User")
        student = OldUser.objects.create(
            username="migration-student",
            email="migration-student@example.com",
            is_student=True,
        )
        mixed = OldUser.objects.create(
            username="migration-mixed",
            email="migration-mixed@example.com",
            is_student=True,
            is_instructor=True,
        )
        applicant = OldUser.objects.create(
            username="migration-applicant",
            email="migration-applicant@example.com",
        )

        MigrationExecutor(connection).migrate(latest)
        assert (
            User.objects.get(pk=student.pk).retain_student_account_on_next_edition_reset
            is False
        )
        assert (
            User.objects.get(pk=mixed.pk).retain_student_account_on_next_edition_reset
            is None
        )
        assert (
            User.objects.get(
                pk=applicant.pk
            ).retain_student_account_on_next_edition_reset
            is None
        )
    finally:
        MigrationExecutor(connection).migrate(latest)
