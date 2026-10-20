import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib import admin
from django.core.management import call_command
from django.db import IntegrityError, transaction

from portal.users.admin import UserAdmin
from portal.users.models import User

pytestmark = pytest.mark.django_db


def deploy_key_pair(size):
    key = rsa.generate_private_key(public_exponent=65537, key_size=size)
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf8")
    public_key = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH,
        )
        .decode("utf8")
    )
    return private_key, public_key


def test_new_users_receive_matching_4096_bit_deploy_keys():
    user = User.objects.create_user(
        username="key-policy",
        email="key-policy@example.com",
    )

    private_key = serialization.load_pem_private_key(
        user.deploy_private_key.encode("utf8"), password=None
    )
    public_key = serialization.load_ssh_public_key(
        user.deploy_public_key.encode("utf8")
    )

    assert private_key.key_size == 4096
    assert public_key.key_size == 4096
    assert private_key.public_key().public_numbers() == public_key.public_numbers()


def test_rotate_deploy_keys_is_dry_run_by_default(capsys):
    user = User.objects.create_user(
        username="legacy-key-dry-run",
        email="legacy-key-dry-run@example.com",
        is_student=True,
    )
    old_private_key, old_public_key = deploy_key_pair(2048)
    User.objects.filter(pk=user.pk).update(
        deploy_private_key=old_private_key,
        deploy_public_key=old_public_key,
    )

    call_command("rotate-deploy-keys", users=[user.email])

    user.refresh_from_db()
    assert user.deploy_private_key == old_private_key
    assert user.deploy_public_key == old_public_key
    assert "Dry run" in capsys.readouterr().out


def test_rotate_deploy_keys_changes_only_the_matching_pair():
    user = User.objects.create_user(
        username="legacy-key-apply",
        email="legacy-key-apply@example.com",
        name="Keep every other field",
        github_username="keep-this-too",
        is_student=True,
    )
    old_private_key, old_public_key = deploy_key_pair(2048)
    User.objects.filter(pk=user.pk).update(
        deploy_private_key=old_private_key,
        deploy_public_key=old_public_key,
    )
    user.refresh_from_db()
    unchanged_fields = {
        field.attname: getattr(user, field.attname)
        for field in User._meta.concrete_fields
        if field.name not in {"deploy_private_key", "deploy_public_key"}
    }

    call_command("rotate-deploy-keys", users=[user.email], apply=True)

    user.refresh_from_db()
    private_key = serialization.load_pem_private_key(
        user.deploy_private_key.encode("utf8"), password=None
    )
    public_key = serialization.load_ssh_public_key(
        user.deploy_public_key.encode("utf8")
    )
    assert private_key.key_size == 4096
    assert public_key.key_size == 4096
    assert private_key.public_key().public_numbers() == public_key.public_numbers()
    assert {
        field.attname: getattr(user, field.attname)
        for field in User._meta.concrete_fields
        if field.name not in {"deploy_private_key", "deploy_public_key"}
    } == unchanged_fields


def test_rotate_deploy_keys_skips_compliant_keys(capsys):
    user = User.objects.create_user(
        username="compliant-key",
        email="compliant-key@example.com",
        is_student=True,
    )
    original_pair = (user.deploy_private_key, user.deploy_public_key)

    call_command("rotate-deploy-keys", users=[user.email], apply=True)

    user.refresh_from_db()
    assert (user.deploy_private_key, user.deploy_public_key) == original_pair
    assert "0 key pair(s) rotated, 1 already compliant" in capsys.readouterr().out


def test_rotate_all_current_students_excludes_other_accounts():
    current_student = User.objects.create_user(
        username="current-student-key",
        email="current-student-key@example.com",
        is_student=True,
    )
    excluded = [
        User.objects.create_user(
            username="inactive-student-key",
            email="inactive-student-key@example.com",
            is_student=True,
            is_active=False,
        ),
        User.objects.create_user(
            username="applicant-key",
            email="applicant-key@example.com",
        ),
        User.objects.create_user(
            username="instructor-key",
            email="instructor-key@example.com",
            is_student=True,
            is_instructor=True,
        ),
    ]
    old_private_key, old_public_key = deploy_key_pair(2048)
    User.objects.filter(pk__in=[current_student.pk, *(u.pk for u in excluded)]).update(
        deploy_private_key=old_private_key,
        deploy_public_key=old_public_key,
    )

    call_command("rotate-deploy-keys", all_current_students=True, apply=True)

    current_student.refresh_from_db()
    assert current_student.deploy_public_key != old_public_key
    for user in excluded:
        user.refresh_from_db()
        assert user.deploy_private_key == old_private_key
        assert user.deploy_public_key == old_public_key


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
