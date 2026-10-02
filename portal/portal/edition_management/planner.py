import hashlib
import json

from constance import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from portal.users.models import User

from .maintenance import deployment_ready, state, superuser
from .models import EditionRun, GradingJob
from .policy import CLEAR, KEEP, SELECTIVE, UPDATED_FIELDS, model

PENDING_GRADING = ("sent", "grading")
GRADING_MODELS = ("academy.Grade", "applications.Submission")


def database_identity():
    db = settings.DATABASES["default"]
    return f'{db["HOST"]}:{db.get("PORT") or 5432}/{db["NAME"]}'


def organizers():
    return User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(is_instructor=True)
    ).order_by("username")


def protected_ids(actor):
    return {
        actor.pk,
        *User.objects.filter(username__in=settings.EDITION_SERVICE_USERS).values_list(
            "pk", flat=True
        ),
    }


def unfinished_grading_records():
    rows = [
        {
            "model": label,
            "count": model(label).objects.filter(status__in=PENDING_GRADING).count(),
        }
        for label in GRADING_MODELS
    ]
    return {"total": sum(row["count"] for row in rows), "rows": rows}


def validate_jobs():
    """Block active or unverifiable graders, then report abandoned database states."""
    from .jobs import scan_existing_jobs

    scan_existing_jobs()
    if GradingJob.objects.exclude(status="finished").exists():
        raise ValidationError(
            "External grading jobs have not finished. Wait for the worker's job check."
        )
    return unfinished_grading_records()


def snapshot_digest(labels, excluded_fields=None):
    """Hash complete rows without persisting passwords, keys or personal records."""
    digest = hashlib.sha256()
    for label in sorted(labels):
        cls = model(label)
        digest.update(label.encode())
        fields = [
            f.attname
            for f in cls._meta.concrete_fields
            if f.attname not in (excluded_fields or {}).get(label, set())
        ]
        for row in cls.objects.order_by("pk").values(*fields).iterator():
            digest.update(json.dumps(row, default=str, sort_keys=True).encode())
    return digest.hexdigest()


def plan(actor, retained):
    superuser(actor)
    deployment_ready()
    retained = set(map(int, retained)) | protected_ids(actor)
    allowed = set(organizers().values_list("pk", flat=True)) | protected_ids(actor)
    if retained - allowed:
        raise ValidationError(
            "Only existing organizers and protected accounts can be retained."
        )
    mode = config.ADMISSIONS_MODE
    users = list(
        User.objects.order_by("pk").values(
            "id",
            "username",
            "date_joined",
            "is_student",
            "is_staff",
            "is_superuser",
            "is_instructor",
        )
    )
    delete = [u for u in users if u["id"] not in retained]
    rows = []
    owner_fields = {
        "users.User": "pk",
        "account.EmailAddress": "user_id",
        "socialaccount.SocialAccount": "user_id",
        "socialaccount.SocialToken": "account__user_id",
        "authtoken.Token": "user_id",
        "admin.LogEntry": "user_id",
    }
    for label in sorted(set(CLEAR + KEEP + SELECTIVE)):
        queryset = model(label).objects.all()
        total = queryset.count()
        deleted = (
            total
            if label in CLEAR
            else (
                queryset.exclude(**{owner_fields[label] + "__in": retained}).count()
                if label in owner_fields
                else 0
            )
        )
        rows.append(
            {
                "model": label,
                "count": total,
                "delete": deleted,
                "keep": total - deleted,
                "configure": total if label in UPDATED_FIELDS else None,
            }
        )
    # All non-student candidates are explicitly reviewed, including recent signups.
    review = [u["username"] for u in delete if not u["is_student"]]
    result = {
        "database": database_identity(),
        "release": settings.EDITION_RELEASE,
        "generation": state().generation,
        "retained": sorted(retained),
        "retained_names": [u["username"] for u in users if u["id"] in retained],
        "deleted_names": [u["username"] for u in delete],
        "review": review,
        "rows": rows,
        "unfinished_grading": unfinished_grading_records(),
        "mode": mode,
        "digest": snapshot_digest(
            set(CLEAR + KEEP + SELECTIVE) - {"sessions.Session", "admin.LogEntry"}
        ),
    }
    return result


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


def create_preview(actor, retained):
    from .maintenance import lock

    with lock(exclusive=True):
        if state().phase != "maintenance":
            raise ValidationError(
                "Enter maintenance before preparing the final preview."
            )
        if EditionRun.objects.filter(status__in=("queued", "running")).exists():
            raise ValidationError("Another operation is already queued or running.")
        data = plan(actor, retained)
        return EditionRun.objects.create(
            actor=actor,
            actor_username=actor.username,
            database=data["database"],
            release=data["release"],
            generation=data["generation"],
            plan=data,
            fingerprint=fingerprint(data),
        )


def require_worker():
    current = state()
    if (
        not current.worker_seen
        or (timezone.now() - current.worker_seen).total_seconds() > 30
        or current.worker_release != settings.EDITION_RELEASE
    ):
        raise ValidationError(
            "The edition worker is not ready. Retry once deployment has completed."
        )
