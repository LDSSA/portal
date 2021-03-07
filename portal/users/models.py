from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class UserWhitelist(models.Model):
    username = models.CharField(_("Username"), max_length=255, unique=True)
    student = models.BooleanField(default=True)


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    logo = models.TextField(blank=True)
    student = models.BooleanField(default=True)
    slack_member_id = models.TextField(blank=True)
    github_username = models.TextField(blank=True)
    deploy_private_key = models.TextField(blank=True)
    deploy_public_key = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
        if not self.deploy_private_key and not self.deploy_public_key:
            key = rsa.generate_private_key(
                backend=crypto_default_backend(),
                public_exponent=65537,
                key_size=2048
            )
            self.deploy_private_key = key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.PKCS8,
                crypto_serialization.NoEncryption()).decode('utf8')

            self.deploy_public_key = key.public_key().public_bytes(
                crypto_serialization.Encoding.OpenSSH,
                crypto_serialization.PublicFormat.OpenSSH).decode('utf8')

        super().save(*args, **kwargs)

