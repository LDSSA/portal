"""Track external graders without assuming that a callback means file I/O ended."""

import json
import subprocess
import threading

from django.db import close_old_connections

from .models import GradingJob


def launch(name, backend, command):
    job = GradingJob.objects.create(name=name, backend=backend)
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        job.status = "finished"
        job.save(update_fields=["status"])
        raise
    job.status = "running"
    job.save(update_fields=["status"])

    def wait():
        code = process.wait()
        close_old_connections()
        try:
            # Successful attached kubectl/docker completion means the container exited.
            GradingJob.objects.filter(pk=name).update(
                status="finished" if code == 0 else "checking"
            )
        finally:
            close_old_connections()

    threading.Thread(target=wait, daemon=True).start()


def refresh_jobs():
    for job in GradingJob.objects.exclude(status="finished"):
        if job.backend == "kubernetes":
            command = [
                "kubectl",
                "get",
                "pod",
                job.name,
                "--ignore-not-found",
                "-o",
                "json",
                "--request-timeout=10s",
            ]
        else:
            command = ["docker", "inspect", job.name]
        try:
            result = subprocess.run(command, capture_output=True, timeout=15)
            if result.returncode:
                continue
            if not result.stdout.strip():
                if job.remote_seen:
                    job.status = "finished"
                    job.save(update_fields=["status"])
                continue
            data = json.loads(result.stdout)
            done = (
                data.get("status", {}).get("phase") in {"Succeeded", "Failed"}
                if job.backend == "kubernetes"
                else not data[0]["State"]["Running"]
            )
            job.remote_seen = True
            if done:
                job.status = "finished"
            job.save(update_fields=["remote_seen", "status"])
        except (OSError, subprocess.TimeoutExpired, ValueError):
            continue  # Fail closed. Never infer completion from a monitoring failure.


def scan_existing_jobs():
    """Discover pre-deployment graders too; a finished callback is not sufficient."""
    from django.conf import settings
    from django.core.exceptions import ValidationError

    backends = {settings.GRADING_CLASS, settings.GRADING_ADMISSIONS_CLASS}
    checks = []
    if any(
        "Kubernetes" in value or value.endswith("AcademyDockerGrading")
        for value in backends
    ):
        checks.append(
            (
                "kubernetes",
                ["kubectl", "get", "pods", "-o", "json", "--request-timeout=10s"],
            )
        )
    if any(value.endswith("AdmissionsDockerGrading") for value in backends):
        checks.append(
            ("docker", ["docker", "ps", "--format", "{{json .}}", "--no-trunc"])
        )
    for backend, command in checks:
        try:
            result = subprocess.run(command, capture_output=True, timeout=15)
            if result.returncode:
                raise ValidationError(
                    "Cannot verify external grading jobs. Check the grader connection before resetting."
                )
            if backend == "kubernetes":
                for pod in json.loads(result.stdout)["items"]:
                    images = [
                        c.get("image", "")
                        for c in pod.get("spec", {}).get("containers", [])
                    ]
                    if any(
                        image.startswith(("ldssa/batch-", "ldssa/dev-batch-"))
                        for image in images
                    ) and pod.get("status", {}).get("phase") not in {
                        "Succeeded",
                        "Failed",
                    }:
                        GradingJob.objects.update_or_create(
                            name=pod["metadata"]["name"],
                            defaults={
                                "backend": backend,
                                "remote_seen": True,
                                "status": "running",
                            },
                        )
            else:
                for line in result.stdout.splitlines():
                    container = json.loads(line)
                    if container.get("Image", "").startswith(
                        ("ldssa/batch-", "ldssa/dev-batch-")
                    ):
                        GradingJob.objects.update_or_create(
                            name=container["Names"],
                            defaults={
                                "backend": backend,
                                "remote_seen": True,
                                "status": "running",
                            },
                        )
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
            raise ValidationError(
                "Cannot verify external grading jobs. No reset may proceed."
            ) from exc
