"""Verify upgrading populated legacy data does not enroll or reclassify anyone."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)


def test_upgrade_preserves_legacy_applicants_and_selections():
    before = [
        ("users", "0022_alter_user_email"),
        ("selection", "0006_auto_20230205_1053"),
    ]
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate(before)
        old_apps = executor.loader.project_state(before).apps
        OldUser = old_apps.get_model("users", "User")
        OldSelection = old_apps.get_model("selection", "Selection")
        user = OldUser.objects.create(
            username="legacy", email="legacy@example.com", ticket_type="regular"
        )
        selection = OldSelection.objects.create(
            user_id=user.pk, status="Accepted", payment_value=500
        )
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        new_apps = executor.loader.project_state(latest).apps
        saved_user = new_apps.get_model("users", "User").objects.get(pk=user.pk)
        saved_selection = new_apps.get_model("selection", "Selection").objects.get(
            pk=selection.pk
        )
        assert saved_user.admissions_mode == "exam"
        assert saved_user.registration_completed_at is None
        assert not saved_user.is_student
        assert saved_selection.status == "Accepted"
        assert saved_selection.payment_value == 500
        assert new_apps.get_model("selection", "EnrollmentEmail").objects.count() == 0
    finally:
        MigrationExecutor(connection).migrate(latest)
