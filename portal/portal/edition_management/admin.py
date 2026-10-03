from constance import config
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path

from . import backups
from .configuration import CLOSED_SWITCHES, readiness_issues
from .forms import ConfirmForm, PrepareForm
from .maintenance import (
    MaintenanceBusy,
    cancel_preparation,
    deployment_ready,
    lock,
    state,
    superuser,
)
from .models import EditionRun
from .planner import create_preview, database_identity, require_worker, validate_jobs
from .policy import policy_rows


@admin.register(EditionRun)
class EditionRunAdmin(admin.ModelAdmin):
    list_display = ("created", "kind", "status", "actor_username", "database")
    change_list_template = "admin/edition_management/history.html"

    def has_module_permission(self, request):
        return (
            request.user.is_active
            and request.user.is_staff
            and request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom = [
            path(
                "control/",
                self.admin_site.admin_view(self.control),
                name="edition_control",
            ),
            path(
                "run/<uuid:pk>/",
                self.admin_site.admin_view(self.run_view),
                name="edition_run",
            ),
            path(
                "download/<uuid:pk>/",
                self.admin_site.admin_view(self.download),
                name="edition_download",
            ),
        ]
        return custom + super().get_urls()

    def context(self, request, **extra):
        try:
            deployment_ready()
            readiness = (
                "Migrations complete; this release is enabled for edition operations."
            )
        except ValidationError as exc:
            readiness = "; ".join(exc.messages)
        try:
            backup_dir = str(backups.directory())
        except (ValidationError, OSError):
            backup_dir = ""
        return {
            **self.admin_site.each_context(request),
            "title": "Edition management",
            "opts": self.model._meta,
            "state": state(),
            "database": database_identity(),
            "environment": settings.EDITION_ENVIRONMENT,
            "release": settings.EDITION_RELEASE,
            "readiness": readiness,
            "backup_dir": backup_dir,
            "policy": policy_rows(),
            **extra,
        }

    def control(self, request):
        superuser(request.user)
        form = PrepareForm(request.POST or None, actor=request.user)
        try:
            if request.method == "POST":
                action = request.POST.get("action")
                deployment_ready()
                if action == "preview":
                    if form.is_valid():
                        run = create_preview(
                            request.user,
                            form.cleaned_data["retained"].values_list("pk", flat=True),
                        )
                        return redirect("admin:edition_run", pk=run.pk)
                else:
                    with lock(exclusive=True):
                        if EditionRun.objects.filter(
                            status__in=("queued", "running")
                        ).exists():
                            raise ValidationError(
                                "Wait for the active operation to finish."
                            )
                        current = state()
                        if action == "maintenance":
                            unfinished = validate_jobs()
                            if current.phase == "prepared":
                                raise ValidationError(
                                    "This edition was already reset. Review and open it before starting another edition."
                                )
                            current.phase = "maintenance"
                            current.save(update_fields=["phase"])
                            if unfinished["total"]:
                                messages.warning(
                                    request,
                                    "Unfinished grading records with no active external grader "
                                    f'were found ({unfinished["total"]}). They will be listed '
                                    "in the preview and removed by the reset.",
                                )
                        elif action == "cancel":
                            cancel_preparation()
                        elif action == "open":
                            if (
                                current.phase != "prepared"
                                or request.POST.get("confirmed") != "yes"
                            ):
                                raise ValidationError(
                                    "Review and confirm opening the prepared edition."
                                )
                            issues = readiness_issues()
                            if issues:
                                raise ValidationError(issues)
                            from django.db import transaction

                            with transaction.atomic():
                                for key in CLOSED_SWITCHES:
                                    setattr(config, key, True)
                                current.phase = "open"
                                current.save(update_fields=["phase"])
                                self.log_change(
                                    request,
                                    EditionRun.objects.filter(
                                        kind="reset", status="succeeded"
                                    ).first(),
                                    "Opened prepared edition",
                                )
                        elif action in ("backup", "purge"):
                            require_worker()
                            backups.directory()
                            if (
                                action == "purge"
                                and request.POST.get("confirmed") != "yes"
                            ):
                                raise ValidationError(
                                    "Confirm deletion of the temporary database dumps."
                                )
                            run = EditionRun.objects.create(
                                kind=action,
                                status="queued",
                                actor=request.user,
                                actor_username=request.user.username,
                                release=settings.EDITION_RELEASE,
                                database=database_identity(),
                                generation=current.generation,
                            )
                            return redirect("admin:edition_run", pk=run.pk)
                        else:
                            raise ValidationError("Unknown action.")
                    return redirect("admin:edition_control")
        except (ValidationError, MaintenanceBusy, OSError) as exc:
            messages.error(
                request,
                "; ".join(exc.messages)
                if isinstance(exc, ValidationError)
                else str(exc),
            )
        return TemplateResponse(
            request,
            "admin/edition_management/control.html",
            self.context(
                request,
                form=form,
                runs=EditionRun.objects.all()[:20],
                mode=config.ADMISSIONS_MODE,
            ),
        )

    def run_view(self, request, pk):
        superuser(request.user)
        run = get_object_or_404(EditionRun, pk=pk)
        form = ConfirmForm(request.POST or None)
        try:
            if request.method == "POST" and form.is_valid():
                with lock(exclusive=True):
                    run.refresh_from_db()
                    if run.status in ("queued", "running", "succeeded"):
                        return redirect("admin:edition_run", pk=run.pk)
                    if (
                        run.status != "draft"
                        or run.kind != "reset"
                        or run.actor_id != request.user.pk
                    ):
                        raise ValidationError(
                            "Only the preparing administrator can confirm this draft."
                        )
                    deployment_ready()
                    require_worker()
                    validate_jobs()
                    from .planner import fingerprint, plan

                    if (
                        state().phase != "maintenance"
                        or fingerprint(plan(request.user, run.plan["retained"]))
                        != run.fingerprint
                    ):
                        raise ValidationError(
                            "The preview changed. Prepare a new preview."
                        )
                    if EditionRun.objects.filter(
                        status__in=("queued", "running")
                    ).exists():
                        raise ValidationError("Another operation is active.")
                    run.backup_first = form.cleaned_data["backup_first"]
                    if run.backup_first:
                        backups.directory()
                    run.status = "queued"
                    run.save(update_fields=["backup_first", "status"])
                    return redirect("admin:edition_run", pk=run.pk)
        except (ValidationError, MaintenanceBusy, OSError) as exc:
            messages.error(
                request,
                "; ".join(exc.messages)
                if isinstance(exc, ValidationError)
                else str(exc),
            )
        return TemplateResponse(
            request,
            "admin/edition_management/run.html",
            self.context(request, run=run, form=form),
        )

    def download(self, request, pk):
        superuser(request.user)
        if request.method != "GET":
            raise Http404
        run = get_object_or_404(EditionRun, pk=pk)
        try:
            with lock():
                handle = backups.open_dump(run)
        except (ValidationError, MaintenanceBusy):
            raise Http404("Backup unavailable")
        response = FileResponse(
            handle,
            as_attachment=True,
            filename=run.backup_name,
            content_type="application/octet-stream",
        )
        response["Cache-Control"] = "no-store, private"
        return response
