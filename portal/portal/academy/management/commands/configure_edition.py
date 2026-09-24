"""Preview/apply the single active edition's calendar without deleting records."""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from constance import config
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.academy.models import Grade, Unit
from portal.hackathons.models import Attendance, Hackathon, Submission, Team

LISBON = ZoneInfo("Europe/Lisbon")
SPECIALIZATIONS = {
    "S01": ("2026-10-25", "2026-11-21"),
    "S02": ("2026-11-23", "2026-12-19"),
    "S03": ("2027-01-05", "2027-01-31"),
    "S04": ("2027-02-02", "2027-02-28"),
    "S05": ("2027-03-02", "2027-03-27"),
    "S06": ("2027-03-29", "2027-04-24"),
}
HACKATHONS = {
    "HCKT01": "2026-11-22",
    "HCKT03": "2027-02-01",
    "HCKT04": "2027-03-01",
    "HCKT05": "2027-03-28",
    "HCKT06": "2027-04-25",
}
OPTIONAL = {"SLU18", "SLU19", "SLU32", "SLU64"}


def midnight(day):
    return datetime.combine(date.fromisoformat(day), time.min, tzinfo=LISBON)


class Command(BaseCommand):
    help = "Preview the 2026/27 no-exam calendar. --apply changes configuration and existing curriculum dates only."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument(
            "--hackathon-2-date",
            default="2026-12-20",
            help="Hackathon 2 date; defaults to the confirmed 20 December 2026.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            h2 = date.fromisoformat(options["hackathon_2_date"])
        except ValueError as exc:
            raise CommandError("Use YYYY-MM-DD for Hackathon 2.") from exc
        if h2 <= date(2026, 12, 19):
            raise CommandError(
                "Hackathon 2 must follow the specialization 2 deadline (2026-12-19)."
            )
        values = {
            "NO_EXAM_SIGNUPS_START": midnight("2026-09-24"),
            "NO_EXAM_SIGNUPS_END": midnight("2026-10-16"),
            "NO_EXAM_REGISTRATION_END": midnight("2026-10-16"),
            "NO_EXAM_PAYMENTS_START": midnight("2026-10-12"),
            "NO_EXAM_PAYMENTS_END": midnight("2026-10-18"),
            "ACADEMY_START": midnight("2026-10-18"),
        }
        for key, value in values.items():
            self.stdout.write(f"{key} = {value.isoformat()}")
        for code, (start, end) in SPECIALIZATIONS.items():
            self.stdout.write(
                f"{code}: opens {start}; certificate deadline {end}, end of Lisbon day"
            )
        hackathons = {**HACKATHONS, "HCKT02": h2.isoformat()}
        for code, day in sorted(hackathons.items()):
            self.stdout.write(
                f"{code}: {day}; status closed until staff operate the event"
            )
        self.stdout.write(
            "SLU01–17 mandatory; SLU18/19/32/64 optional. Mode: no_exam; manual switches enabled; date windows enforced."
        )
        if not options["apply"]:
            self.stdout.write("Preview only. No database changes.")
            return
        if (
            Grade.objects.exists()
            or Submission.objects.exists()
            or Attendance.objects.exists()
            or Team.objects.exists()
        ):
            raise CommandError(
                "Historical course activity exists. Archive/reset the edition first; this command never deletes it."
            )
        expected = (
            {f"SLU{i:02}" for i in range(1, 20)}
            | {"SLU32", "SLU64"}
            | {f"BLU{i:02}" for i in range(1, 16)}
        )
        missing = expected - set(Unit.objects.values_list("code", flat=True))
        missing_h = set(hackathons) - set(
            Hackathon.objects.values_list("code", flat=True)
        )
        if missing or missing_h:
            raise CommandError(
                f"Import curriculum metadata first. Missing units: {sorted(missing)}; hackathons: {sorted(missing_h)}"
            )
        for code, (start, end) in SPECIALIZATIONS.items():
            codes = (
                ({f"SLU{i:02}" for i in range(1, 20)} | {"SLU32", "SLU64"})
                if code == "S01"
                else {
                    f"BLU{i:02}"
                    for i in range(
                        (int(code[1:]) - 2) * 3 + 1, (int(code[1:]) - 1) * 3 + 1
                    )
                }
            )
            if (
                Unit.objects.filter(code__in=codes)
                .exclude(specialization_id=code)
                .exists()
            ):
                raise CommandError(
                    f"Correct unit-to-specialization assignments for {code} before applying."
                )
            Unit.objects.filter(code__in=codes).update(
                available_on=start,
                due_date=end,
                open=True,
                required_for_certificate=True,
            )
        Unit.objects.filter(code__in=OPTIONAL).update(required_for_certificate=False)
        for code, day in hackathons.items():
            Hackathon.objects.filter(pk=code).update(due_date=day, status="closed")
        for key, value in values.items():
            setattr(config, key, value)
        config.ADMISSIONS_MODE = "no_exam"
        config.NO_EXAM_USE_SCHEDULE = True
        config.ACCOUNT_ALLOW_REGISTRATION = True
        config.NO_EXAM_REGISTRATION_OPEN = True
        config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS = True
        config.NO_EXAM_ACADEMY_ACCESS_OPEN = True
        self.stdout.write(
            "Calendar applied. Existing users retain their admissions mode; no emails sent."
        )
