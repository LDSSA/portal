"""Forms for the users app."""

import logging

import django.contrib.auth.forms

# from allauth.account.forms import SignupForm
from constance import config

# from allauth.account.forms import SignupForm
from django import forms
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from portal.users.models import Gender, TicketType, TicketTypeSelectable

User = get_user_model()
logger = logging.getLogger(__name__)


class UserChangeForm(forms.ModelForm):
    name = forms.CharField()

    def __init__(self, *args, **kwawgs) -> None:
        super().__init__(*args, **kwawgs)
        if config.PORTAL_STATUS == "academy":
            del self.fields["gender"]
            del self.fields["profession"]
            del self.fields["company"]
            del self.fields["ticket_type"]

        else:
            del self.fields["logo"]
            del self.fields["github_username"]
            del self.fields["slack_member_id"]
            if config.PORTAL_STATUS not in (
                "admissions",
                "admissions:applications",
            ):
                self.fields["ticket_type"] = forms.ChoiceField(
                    choices=TicketType.choices,
                    disabled=True,
                )

    class Meta:
        model = User
        fields = (
            "name",
            "logo",
            "github_username",
            "slack_member_id",
            "gender",
            "profession",
            "company",
            "ticket_type",
        )
        widgets = {
            "logo": forms.TextInput(),
            "github_username": forms.TextInput(),
            "slack_member_id": forms.TextInput(),
        }


class UserCreationForm(django.contrib.auth.forms.UserCreationForm):
    class Meta(auth.forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(_("A user with that username already exists."))


class PortalSignupForm(forms.Form):
    name = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # del self.fields["username"].widget.attrs["autofocus"]
        self.fields["gender"] = forms.ChoiceField(choices=Gender.choices)
        self.fields["ticket_type"] = forms.ChoiceField(
            choices=TicketTypeSelectable.choices
        )
        self.fields["profession"] = forms.CharField(max_length=50, required=False)
        self.fields["company"] = forms.CharField(max_length=100, required=False)

    def signup(self, request, user) -> None:
        user.name = self.cleaned_data["name"]
        user.gender = self.cleaned_data["gender"]
        user.ticket_type = self.cleaned_data["ticket_type"]
        user.profession = self.cleaned_data["profession"]
        user.company = self.cleaned_data["company"]
        user.save()
