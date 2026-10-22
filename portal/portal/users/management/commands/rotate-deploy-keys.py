"""Replace obsolete student deploy keys without modifying any other user data."""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_ssh_public_key
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.users.models import (
    DEPLOY_RSA_KEY_SIZE,
    User,
    generate_deploy_key_pair,
)

GITHUB_MINIMUM_RSA_KEY_SIZE = 3072


def rsa_key_size(public_key):
    try:
        key = load_ssh_public_key(public_key.encode("utf8"))
    except (TypeError, ValueError):
        return None
    return key.key_size if isinstance(key, rsa.RSAPublicKey) else None


class Command(BaseCommand):
    help = (
        "Rotate undersized student RSA deploy keys (dry run unless --apply). "
        "Only the deploy_private_key and deploy_public_key columns are changed."
    )

    def add_arguments(self, parser):
        selector = parser.add_mutually_exclusive_group(required=True)
        selector.add_argument(
            "--user",
            action="append",
            dest="users",
            metavar="EMAIL",
            help="Exact student email address; may be supplied more than once.",
        )
        selector.add_argument(
            "--all-current-students",
            action="store_true",
            help="Select active student-only accounts.",
        )
        parser.add_argument("--apply", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        students = User.objects.select_for_update().order_by("pk")
        if options["all_current_students"]:
            students = students.filter(
                is_active=True,
                is_student=True,
                is_instructor=False,
                is_staff=False,
                is_superuser=False,
            )
        else:
            requested = set(options["users"])
            students = students.filter(email__in=requested)
            found = set(students.values_list("email", flat=True))
            missing = sorted(requested - found)
            if missing:
                raise CommandError("No account found for: " + ", ".join(missing))

        selected = list(students)
        rotations = []
        for student in selected:
            size = rsa_key_size(student.deploy_public_key)
            if size is None or size < GITHUB_MINIMUM_RSA_KEY_SIZE:
                rotations.append((student, size))

        action = "Rotating" if options["apply"] else "Would rotate"
        for student, old_size in rotations:
            old_description = f"{old_size}-bit RSA" if old_size else "invalid/non-RSA"
            self.stdout.write(
                f"{action} user {student.pk} ({student.email}): "
                f"{old_description} -> {DEPLOY_RSA_KEY_SIZE}-bit RSA"
            )
            if options["apply"]:
                private_key, public_key = generate_deploy_key_pair()
                User.objects.filter(pk=student.pk).update(
                    deploy_private_key=private_key,
                    deploy_public_key=public_key,
                )

        compliant = len(selected) - len(rotations)
        self.stdout.write(
            f"Selected {len(selected)} account(s): {len(rotations)} key pair(s) "
            f"{'rotated' if options['apply'] else 'need rotation'}, "
            f"{compliant} already compliant."
        )
        if rotations and not options["apply"]:
            self.stdout.write("Dry run; pass --apply with the same selector to save.")
