from cryptography.hazmat.backends import (
    default_backend as crypto_default_backend,
)
from cryptography.hazmat.primitives import (
    serialization as crypto_serialization,
)
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserWhitelist(models.Model):
    username = models.CharField(_("Username"), max_length=255, unique=True)
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.username}"


class Gender(models.TextChoices):
    female = "female", _("Female")
    male = "male", _("Male")
    other = "other", _("Other/Prefer not to say")


class TicketTypeSelectable(models.TextChoices):
    student = "student", _("Student")
    regular = "regular", _("Regular")
    company = "company", _("Company")


class TicketType(models.TextChoices):
    student = "student", _("Student")
    regular = "regular", _("Regular")
    company = "company", _("Company")
    scholarship = "scholarship", _("Scholarship")


# Preference for in-person or remote
class AcademyTypePreference(models.TextChoices):
    in_person_then_remote = "in_person_then_remote", _("In-person then remote")
    remote_then_in_person = "remote_then_in_person", _("Remote then in-person")
    remote_only = "remote_only", _("Remote only")
    in_person_only = "in_person_only", _("In-person only")


class AdmissionsMode(models.TextChoices):
    EXAM = "exam", _("Exam")
    NO_EXAM = "no_exam", _("No exam")


# TODO: custom user manager to filter out users with unverified email addresses
class User(AbstractUser):
    hackathon_submissions = GenericRelation("hackathons.Submission")

    email = models.EmailField(unique=True, null=False)
    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Academy
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)
    retain_account_on_next_edition_reset = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Retain account on next edition reset"),
        help_text=_(
            "Student-only and roleless accounts: select to preserve the complete "
            "user account during the next edition reset. The student's role, when "
            "present, is preserved, but academic and admissions activity is still "
            "deleted. After a successful reset, this setting returns to unselected "
            "and must be authorized again for a later reset. Staff, superusers, "
            "instructors, and mixed-role accounts use the organizer policy instead."
        ),
    )
    slack_member_id = models.TextField(blank=True)
    github_username = models.TextField(blank=True)
    deploy_private_key = models.TextField(blank=True)
    deploy_public_key = models.TextField(blank=True)

    # Admissions: snapshot the mode at signup; changing the default is not a migration.
    admissions_mode = models.CharField(
        max_length=10,
        choices=AdmissionsMode.choices,
        default=AdmissionsMode.EXAM,
        editable=False,
    )
    registration_completed_at = models.DateTimeField(
        null=True, blank=True, editable=False
    )

    @property
    def admissions_requires_exam(self):
        return self.admissions_mode == AdmissionsMode.EXAM

    code_of_conduct_accepted = models.BooleanField(default=False)
    applying_for_scholarship = models.BooleanField(default=None, null=True)
    academy_type_preference = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        choices=AcademyTypePreference.choices,
    )
    profession = models.CharField(blank=True, max_length=50)
    gender = models.CharField(null=False, max_length=25, choices=Gender.choices)
    ticket_type = models.CharField(
        null=False, max_length=25, choices=TicketType.choices
    )
    company = models.CharField(blank=True, max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Academy graduation eligibility fields
    can_graduate = models.BooleanField(default=True)
    can_attend_next = models.BooleanField(default=True)

    failed_or_dropped = models.BooleanField(default=False)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                name="users_reset_retention_matches_role",
                check=(
                    Q(
                        is_staff=False,
                        is_superuser=False,
                        is_instructor=False,
                        retain_account_on_next_edition_reset__isnull=False,
                    )
                    | (
                        ~Q(
                            is_staff=False,
                            is_superuser=False,
                            is_instructor=False,
                        )
                        & Q(retain_account_on_next_edition_reset__isnull=True)
                    )
                ),
            )
        ]

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def can_choose_reset_retention(self):
        return not (self.is_staff or self.is_superuser or self.is_instructor)

    def _normalize_reset_retention(self):
        previous = self.retain_account_on_next_edition_reset
        if self.can_choose_reset_retention:
            if previous is None:
                self.retain_account_on_next_edition_reset = False
        else:
            self.retain_account_on_next_edition_reset = None
        return previous != self.retain_account_on_next_edition_reset

    def clean(self):
        super().clean()
        self._normalize_reset_retention()

    def save(self, *args, **kwargs):
        retention_changed = self._normalize_reset_retention()
        if retention_changed and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = {
                *kwargs["update_fields"],
                "retain_account_on_next_edition_reset",
            }
        if not self.deploy_private_key and not self.deploy_public_key:
            key = rsa.generate_private_key(
                backend=crypto_default_backend(),
                public_exponent=65537,
                key_size=2048,
            )
            self.deploy_private_key = key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.PKCS8,
                crypto_serialization.NoEncryption(),
            ).decode("utf8")

            self.deploy_public_key = (
                key.public_key()
                .public_bytes(
                    crypto_serialization.Encoding.OpenSSH,
                    crypto_serialization.PublicFormat.OpenSSH,
                )
                .decode("utf8")
            )

        super().save(*args, **kwargs)
