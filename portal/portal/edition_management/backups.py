"""Private, database-scoped temporary dumps; no shell or user-supplied paths."""

import hashlib
import os
import re
import stat
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone

from .planner import database_identity

NAME = re.compile(r"portal-\d{8}T\d{12}Z-[0-9a-f]{32}\.dump\Z")


def directory():
    configured = settings.EDITION_BACKUP_DIR
    if not configured or not Path(configured).is_absolute():
        raise ValidationError(
            "The server backup directory must be a configured absolute path."
        )
    root = Path(configured)
    if root.is_symlink():
        raise ValidationError("The backup directory must not be a symbolic link.")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    scope = hashlib.sha256(database_identity().encode()).hexdigest()[:16]
    path = root / scope
    if path.is_symlink():
        raise ValidationError("The backup directory must not be a symbolic link.")
    path.mkdir(mode=0o700, exist_ok=True)
    path.chmod(0o700)
    return path


def dump(run):
    if connection.vendor != "postgresql":
        raise ValidationError("Backups require PostgreSQL.")
    db = settings.DATABASES["default"]
    env = os.environ.copy()
    # Do not inherit a different database/service definition from the shell.
    for key in list(env):
        if key.startswith("PG"):
            del env[key]
    env.update(
        PGDATABASE=str(db["NAME"]),
        PGUSER=str(db["USER"]),
        PGPASSWORD=str(db["PASSWORD"] or ""),
        PGHOST=str(db["HOST"] or ""),
        PGPORT=str(db.get("PORT") or 5432),
        PGCONNECT_TIMEOUT="15",
    )
    for key, value in db.get("OPTIONS", {}).items():
        if key in {"sslmode", "sslcert", "sslkey", "sslrootcert"}:
            env["PG" + key.upper()] = str(value)
    name = f'portal-{timezone.now().strftime("%Y%m%dT%H%M%S%fZ")}-{run.pk.hex}.dump'
    target = directory() / name
    partial = target.with_suffix(".partial")
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            result = subprocess.run(
                ["pg_dump", "--format=custom", "--no-password"],
                env=env,
                stdout=output,
                stderr=subprocess.PIPE,
                timeout=settings.EDITION_BACKUP_TIMEOUT,
            )
            if result.returncode:
                raise ValidationError(
                    "pg_dump failed; no reset was performed. Check database access, disk space and client/server versions."
                )
            output.flush()
            os.fsync(output.fileno())
        check = subprocess.run(
            ["pg_restore", "--list", str(partial)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        if check.returncode or not partial.stat().st_size:
            raise ValidationError(
                "Backup archive validation failed; no reset was performed."
            )
        sha = hashlib.sha256()
        with partial.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                sha.update(chunk)
        partial.rename(target)
        run.backup_name = name
        run.backup_sha256 = sha.hexdigest()
        run.backup_bytes = target.stat().st_size
        run.save(update_fields=["backup_name", "backup_sha256", "backup_bytes"])
    finally:
        partial.unlink(missing_ok=True)


def open_dump(run):
    if run.backup_deleted or not NAME.fullmatch(run.backup_name):
        raise ValidationError("This backup is no longer available.")
    try:
        fd = os.open(directory() / run.backup_name, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValidationError(
            "The temporary backup is unavailable; the pod may have been replaced."
        ) from exc
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValidationError("Invalid backup file.")
    return os.fdopen(fd, "rb")


def purge():
    """Only generated dump/partial files in THIS database's private directory."""
    removed = 0
    for path in directory().iterdir():
        normalized = path.with_suffix(".dump").name
        if path.suffix not in {".dump", ".partial"} or not NAME.fullmatch(normalized):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        path.unlink()
        removed += 1
    from .models import EditionRun

    EditionRun.objects.exclude(backup_name="").update(backup_deleted=True)
    return removed
