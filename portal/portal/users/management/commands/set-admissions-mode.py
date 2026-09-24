"""Safely convert a pristine existing account; never rewrite an active application."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.applications.models import Application, Submission
from portal.selection.models import Selection
from portal.users.models import AdmissionsMode, User


class Command(BaseCommand):
    help = "Change one untouched applicant's mode (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("--user", required=True, help="Exact email address")
        parser.add_argument("--mode", choices=AdmissionsMode.values, required=True)
        parser.add_argument("--apply", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            user = User.objects.select_for_update().get(email=options["user"])
        except User.DoesNotExist as exc:
            raise CommandError("Applicant not found.") from exc
        application = Application.objects.filter(user=user).first()
        if (
            user.is_staff
            or user.is_superuser
            or user.is_instructor
            or user.is_student
            or user.code_of_conduct_accepted
            or user.applying_for_scholarship is not None
            or user.academy_type_preference
            or user.registration_completed_at
            or Selection.objects.filter(user=user).exists()
            or (
                application
                and (
                    application.coding_test_started_at
                    or application.application_over_email_sent
                )
            )
            or Submission.objects.filter(user=user).exists()
            or (
                application
                and Submission.objects.filter(application=application).exists()
            )
        ):
            raise CommandError(
                "This account has admissions activity or a staff/student role; conversion refused."
            )
        self.stdout.write(f"{user.email}: {user.admissions_mode} -> {options['mode']}")
        if options["apply"]:
            user.admissions_mode = options["mode"]
            user.save(update_fields=["admissions_mode", "updated_at"])
        else:
            self.stdout.write("Dry run; pass --apply to save.")
