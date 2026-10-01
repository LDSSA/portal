from constance import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from . import backups
from .configuration import close_public_access
from .maintenance import deployment_ready, lock, state, superuser
from .models import EditionRun
from .planner import (
    database_identity,
    fingerprint,
    plan,
    snapshot_digest,
    validate_jobs,
)
from .policy import CLEAR, KEEP, UPDATED_FIELDS, model


def execute_reset(run):
    """Execute under the exclusive gate; finish the backup before any deletion."""
    deployment_ready()
    superuser(run.actor)
    validate_jobs()
    if state().phase != "maintenance" or state().generation != run.generation:
        raise ValidationError("The reset generation or maintenance state changed.")
    if run.release != settings.EDITION_RELEASE or run.database != database_identity():
        raise ValidationError("The release or database changed. Prepare a new preview.")
    if fingerprint(plan(run.actor, run.plan["retained"])) != run.fingerprint:
        raise ValidationError(
            "Records changed after preview. Prepare and approve a new preview."
        )
    if run.backup_first:
        backups.dump(run)
    with transaction.atomic():
        current = type(state()).objects.select_for_update().get(pk=1)
        run = EditionRun.objects.select_for_update().get(pk=run.pk)
        preserved = {
            label: set(model(label).objects.values_list("pk", flat=True))
            for label in KEEP
        }
        preserved_values = snapshot_digest(KEEP, UPDATED_FIELDS)
        from rest_framework.authtoken.models import Token

        tokens = dict(
            Token.objects.filter(user_id__in=run.plan["retained"]).values_list(
                "user_id", "key"
            )
        )
        model("academy.Unit").objects.update(instructor=None, open=False)
        model("hackathons.Hackathon").objects.update(status="closed")
        model("capstone.Capstone").objects.update(
            proposal_open=False, report_provisory_open=False, report_final_open=False
        )
        deleted = {}
        for label in CLEAR:
            count, _ = model(label).objects.all().delete()
            deleted[label] = count
        users = model("users.User")
        count, _ = users.objects.exclude(pk__in=run.plan["retained"]).delete()
        deleted["users.User and dependencies"] = count
        users.objects.filter(pk__in=run.plan["retained"]).exclude(
            username__in=settings.EDITION_SERVICE_USERS
        ).update(
            is_student=False,
            registration_completed_at=None,
            code_of_conduct_accepted=False,
            applying_for_scholarship=None,
            academy_type_preference=None,
            ticket_type="",
            can_graduate=True,
            can_attend_next=True,
            failed_or_dropped=False,
            admissions_mode=config.ADMISSIONS_MODE,
        )
        close_public_access()
        for label in CLEAR:
            if model(label).objects.exists():
                raise ValidationError(f"Postcondition failed: {label} is not empty.")
        for label, ids in preserved.items():
            if set(model(label).objects.values_list("pk", flat=True)) != ids:
                raise ValidationError(f"Preservation failed: {label} changed.")
        if snapshot_digest(KEEP, UPDATED_FIELDS) != preserved_values:
            raise ValidationError(
                "Preserved curriculum or configuration values changed."
            )
        if (
            dict(
                Token.objects.filter(user_id__in=run.plan["retained"]).values_list(
                    "user_id", "key"
                )
            )
            != tokens
        ):
            raise ValidationError("Retained API credentials changed.")
        if set(users.objects.values_list("pk", flat=True)) != set(run.plan["retained"]):
            raise ValidationError("Retained accounts changed.")
        current.phase = "prepared"
        current.generation += 1
        current.save(update_fields=["phase", "generation"])
        run.status = "succeeded"
        run.finished = timezone.now()
        run.result = {
            "deleted": deleted,
            "curriculum_preserved": True,
            "public_access": "closed",
        }
        run.save(update_fields=["status", "finished", "result"])


def process(run):
    with lock(exclusive=run.kind == "reset"):
        run.refresh_from_db()
        if run.status != "queued":
            return
        run.status = "running"
        run.save(update_fields=["status"])
        try:
            deployment_ready()
            superuser(run.actor)
            if (
                run.database != database_identity()
                or run.release != settings.EDITION_RELEASE
            ):
                raise ValidationError(
                    "Database or release changed; prepare a new operation."
                )
            if run.kind == "reset":
                execute_reset(run)
                return
            if run.kind == "backup":
                backups.dump(run)
                result = {"archive": "validated", "restore_tested": False}
            elif run.kind == "purge":
                result = {"files_removed": backups.purge()}
            else:
                raise ValidationError("Unknown operation.")
            run.status, run.result = "succeeded", result
        except Exception as exc:
            # No credential-bearing subprocess stderr or raw exception text in reports.
            run.status = "failed"
            run.error = (
                "; ".join(exc.messages)
                if isinstance(exc, ValidationError)
                else "Operation failed. No reset transaction was committed. Consult the server logs."
            )
            import logging

            logging.getLogger(__name__).error(
                "Edition operation %s failed (%s)", run.pk, type(exc).__name__
            )
        run.finished = timezone.now()
        run.save(update_fields=["status", "error", "result", "finished"])
