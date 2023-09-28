from cryptography.hazmat.backends import (
    default_backend as crypto_default_backend,
)
from cryptography.hazmat.primitives import (
    serialization as crypto_serialization,
)
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djchoices import ChoiceItem, DjangoChoices


class UserWhitelist(models.Model):
    username = models.CharField(_("Username"), max_length=255, unique=True)
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)


class Gender(DjangoChoices):
    female = ChoiceItem("female", "Female")
    male = ChoiceItem("male", "Male")
    other = ChoiceItem("other", "Other/Prefer not to say")


class TicketTypeSelectable(DjangoChoices):
    student = ChoiceItem("student", "Student")
    regular = ChoiceItem("regular", "Regular")
    company = ChoiceItem("company", "Company")


class TicketType(DjangoChoices):
    student = ChoiceItem("student", "Student")
    regular = ChoiceItem("regular", "Regular")
    company = ChoiceItem("company", "Company")
    scholarship = ChoiceItem("scholarship", "Scholarship")


# TODO TODO custom user manager to filter out users with unverified email addresses
class User(AbstractUser):
    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Academy
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)
    logo = models.TextField(blank=True)
    slack_member_id = models.TextField(blank=True)
    github_username = models.TextField(blank=True)
    deploy_private_key = models.TextField(blank=True)
    deploy_public_key = models.TextField(blank=True)

    # Admissions
    code_of_conduct_accepted = models.BooleanField(default=False)
    applying_for_scholarship = models.BooleanField(default=None, null=True)
    profession = models.CharField(blank=True, max_length=50)
    gender = models.CharField(null=False, max_length=25, choices=Gender.choices)
    ticket_type = models.CharField(null=False, max_length=25, choices=TicketType.choices)
    company = models.CharField(blank=True, max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Academy graduation eligibility fields
    can_graduate = models.BooleanField(default=True)
    can_attend_next = models.BooleanField(default=True)

    failed_or_dropped = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
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
