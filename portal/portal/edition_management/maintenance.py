"""Database-local cooperative locks, spanning external I/O as well as SQL."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from .models import PortalState

GATE = 194831026
WORKER = 194831027
_depth = ContextVar("edition_gate_depth", default=0)


class MaintenanceBusy(Exception):
    pass


def state():
    return PortalState.objects.get_or_create(pk=1)[0]


def cancel_preparation():
    """Cancel draft resets and resume the current edition atomically."""
    from .models import EditionRun

    with transaction.atomic():
        PortalState.objects.get_or_create(pk=1)
        current = PortalState.objects.select_for_update().get(pk=1)
        if current.phase != "maintenance":
            raise ValidationError("No maintenance preparation to cancel.")
        EditionRun.objects.filter(
            kind="reset",
            status="draft",
        ).update(status="cancelled", finished=timezone.now())
        current.phase = "open"
        current.save(update_fields=["phase"])


def superuser(user):
    if not user or not (
        user.is_authenticated and user.is_active and user.is_staff and user.is_superuser
    ):
        raise PermissionDenied


def schema_ready():
    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise ValidationError(
            "Deploy pending migrations before using edition operations."
        )


@contextmanager
def lock(key=GATE, exclusive=False):
    if key == GATE and not exclusive and _depth.get():
        yield
        return
    if connection.vendor != "postgresql":
        raise MaintenanceBusy("Edition operations require PostgreSQL.")
    suffix = "" if exclusive else "_shared"
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT pg_try_advisory_lock{suffix}(%s)", [key])
        if not cursor.fetchone()[0]:
            raise MaintenanceBusy(
                "Work is still in progress. Try again when it has finished."
            )
    token = _depth.set(_depth.get() + 1) if key == GATE else None
    try:
        yield
    finally:
        if token is not None:
            _depth.reset(token)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT pg_advisory_unlock{suffix}(%s)", [key])


@contextmanager
def operation():
    with lock():
        if state().phase != "open":
            raise MaintenanceBusy("Portal activity is paused for edition maintenance.")
        yield


def guarded(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with operation():
            return function(*args, **kwargs)

    return wrapped


def deployment_ready():
    schema_ready()
    current = state()
    if current.ready_release != settings.EDITION_RELEASE:
        raise ValidationError(
            "The deployment has not completed its edition-readiness check."
        )


def configuration_guard(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with lock():
            if state().phase == "maintenance":
                raise MaintenanceBusy(
                    "Configuration is frozen during reset maintenance."
                )
            return function(*args, **kwargs)

    return wrapped
