import logging
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from constance import config
from django.http import HttpRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail import EmailMessage, EmailMultiAlternatives

from portal.users.models import UserWhitelist


logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)

    def render_mail(self, template_prefix, email, context):
        """
        Renders an e-mail to `email`.  `template_prefix` identifies the
        e-mail that is to be sent, e.g. "account/email/email_confirmation"
        """
        to = [email] if isinstance(email, str) else email
        subject = render_to_string(
            "{0}_subject.txt".format(template_prefix), context
        )
        # remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        from_email = self.get_from_email()

        logger.info(template_prefix)
        template_name = "{0}_message.{1}".format(template_prefix, "txt")
        logger.info(template_name)
        body = render_to_string(
            template_name,
            context,
            self.request,
        ).strip()
        # if "txt" in bodies:
        #     msg = EmailMultiAlternatives(subject, bodies["txt"], from_email, to)
        #     if "html" in bodies:
        #         msg.attach_alternative(bodies["html"], "text/html")
        # else:
        #     msg = EmailMessage(subject, bodies["html"], from_email, to)
        #     msg.content_subtype = "html"  # Main content is now text/html
        msg = EmailMessage(subject, body, from_email, to)
        # msg.content_subtype = "html"  # Main content is now text/html
        return msg

    # def send_mail(self, template_prefix, email, context):
    #     msg = self.render_mail(template_prefix, email, context)
    #     msg.send()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountWhitelistAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(config, "ACCOUNT_ALLOW_REGISTRATION", True)

    def pre_social_login(self, request, sociallogin):
        try:
            UserWhitelist.objects.get(username=sociallogin.user)
        except UserWhitelist.DoesNotExist:
            raise ImmediateHttpResponse(render(request, "whitelist.html"))

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        try:
            obj = UserWhitelist.objects.get(username=sociallogin.user)
            user.is_student = obj.is_student
            user.is_instructor = obj.is_instructor
        except UserWhitelist.DoesNotExist:
            pass
        return user
