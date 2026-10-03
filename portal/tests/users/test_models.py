import pytest
from django.contrib import admin
from django.db import IntegrityError, transaction

from portal.users.admin import UserAdmin
from portal.users.models import User

pytestmark = pytest.mark.django_db


# def test_user_get_absolute_url(user: settings.AUTH_USER_MODEL):
#     assert user.get_absolute_url() == f"/users/{user.username}/"


@pytest.mark.parametrize("role", ["is_instructor", "is_staff", "is_superuser"])
def test_reset_retention_tracks_organizer_role_changes(role):
    user = User.objects.create_user(
        username="role-change",
        email="role-change@example.com",
        is_student=True,
    )
    assert user.retain_account_on_next_edition_reset is False

    user.retain_account_on_next_edition_reset = True
    user.save(update_fields=["retain_account_on_next_edition_reset"])
    setattr(user, role, True)
    user.save(update_fields=[role])
    user.refresh_from_db()
    assert user.retain_account_on_next_edition_reset is None

    setattr(user, role, False)
    user.save(update_fields=[role])
    user.refresh_from_db()
    assert user.retain_account_on_next_edition_reset is False


def test_roleless_retention_carries_into_student_enrollment():
    from portal.selection.enrollment import _activate_student

    user = User.objects.create_user(
        username="newly-enrolled",
        email="newly-enrolled@example.com",
    )
    assert user.retain_account_on_next_edition_reset is False
    user.retain_account_on_next_edition_reset = True
    user.save(update_fields=["retain_account_on_next_edition_reset"])
    _activate_student(user)
    user.refresh_from_db()
    assert user.is_student
    assert user.retain_account_on_next_edition_reset is True


def test_database_rejects_invalid_reset_retention():
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
    roleless = User.objects.create_user(
        username="roleless-constraint",
        email="roleless-constraint@example.com",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=student.pk).update(
            retain_account_on_next_edition_reset=None
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=organizer.pk).update(
            retain_account_on_next_edition_reset=True
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=roleless.pk).update(
            retain_account_on_next_edition_reset=None
        )


def test_admin_edits_retention_for_students_and_roleless_accounts():
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
    field = "retain_account_on_next_edition_reset"

    assert field not in user_admin.get_readonly_fields(None, student)
    assert field in user_admin.get_readonly_fields(None, mixed)
    assert field not in user_admin.get_readonly_fields(None, applicant)


@pytest.mark.django_db(transaction=True)
def test_roleless_reset_retention_data_migration():
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

        through_student_only = [node for node in latest if node[0] != "users"] + [
            ("users", "0024_student_reset_retention")
        ]
        MigrationExecutor(connection).migrate(through_student_only)
        old = (
            MigrationExecutor(connection)
            .loader.project_state(through_student_only)
            .apps
        )
        OldUser = old.get_model("users", "User")
        OldUser.objects.filter(pk=student.pk).update(
            retain_student_account_on_next_edition_reset=True
        )

        MigrationExecutor(connection).migrate(latest)
        assert (
            User.objects.get(pk=student.pk).retain_account_on_next_edition_reset is True
        )
        assert (
            User.objects.get(pk=mixed.pk).retain_account_on_next_edition_reset is None
        )
        assert (
            User.objects.get(pk=applicant.pk).retain_account_on_next_edition_reset
            is False
        )
    finally:
        MigrationExecutor(connection).migrate(latest)
