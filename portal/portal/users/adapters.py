import logging
from typing import Any

from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import EmailAwarePasswordResetTokenGenerator
from allauth.account.models import EmailAddress
from allauth.account.utils import filter_users_by_email, user_pk_to_url_str
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import build_absolute_uri
from constance import config
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from portal.admissions.emails import (
    send_reset_password_email,
    send_signup_email,
)
from portal.users.models import UserWhitelist

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    default_token_generator = EmailAwarePasswordResetTokenGenerator()

    def is_open_for_signup(self, request: HttpRequest):
        if request.path == reverse("instructors_signup"):
            return True
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)

    def clean_email(self, email):
        email = super().clean_email(email)
        if email and app_settings.UNIQUE_EMAIL:
            if EmailAddress.objects.filter(email=email).exists():
                raise ValidationError(
                    "A user is already registered with this e-mail address."
                )
        return email

    def render_mail(self, template_prefix, email, context):
        """Render an e-mail to `email`.

        `template_prefix` identifies the e-mail that is to be sent,
        e.g. "account/email/email_confirmation"
        """
        to = [email] if isinstance(email, str) else email
        subject = render_to_string(f"{template_prefix}_subject.txt", context)
        # remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        from_email = self.get_from_email()

        template_name = "{}_message.{}".format(template_prefix, "txt")
        body = render_to_string(
            template_name,
            context,
            self.request,
        ).strip()
        return EmailMessage(subject, body, from_email, to)

    def send_mail(self, template_prefix, email, context) -> None:
        if template_prefix == "account/email/password_reset_key":
            user = filter_users_by_email(email, is_active=True)[0]
            temp_key = self.default_token_generator.make_token(user)
            path = reverse(
                "account_reset_password_from_key",
                kwargs={"uidb36": user_pk_to_url_str(user), "key": temp_key},
            )
            url = build_absolute_uri(
                request=getattr(self, "request", None), location=path
            )
            send_reset_password_email(to_email=email, reset_password_url=url)
        else:
            super().send_mail(template_prefix, email, context)

    def send_confirmation_mail(
        self,
        request: HttpRequest,
        emailconfirmation,
        signup,
    ) -> None:
        # We assume signup is always True
        send_signup_email(
            to_email=emailconfirmation.email_address.email,
            email_confirmation_url=self.get_email_confirmation_url(
                request, emailconfirmation
            ),
        )


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: Any,
    ):
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountWhitelistAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: Any,
    ):
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)

    def pre_social_login(
        self,
        request: HttpRequest,
        sociallogin,
    ) -> None:
        try:
            UserWhitelist.objects.get(username=sociallogin.user)
        except UserWhitelist.DoesNotExist as exc:
            raise ImmediateHttpResponse(render(request, "whitelist.html")) from exc

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin,
        data,
    ):
        user = super().populate_user(request, sociallogin, data)
        try:
            obj = UserWhitelist.objects.get(username=sociallogin.user)
            user.is_student = obj.is_student
            user.is_instructor = obj.is_instructor
        except UserWhitelist.DoesNotExist:
            pass
        return user
