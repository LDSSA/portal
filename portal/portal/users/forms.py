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
    name = forms.CharField(required=True)
    github_username = forms.CharField(required=True)
    slack_member_id = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove fields based on portal status
        if config.PORTAL_STATUS == "academy":
            fields_to_remove = ["gender", "profession", "company", "ticket_type"]
        else:
            fields_to_remove = ["github_username", "slack_member_id"]
            if config.PORTAL_STATUS not in ("admissions:signup", "admissions:tests"): #maybe during the whole admissions?
                self.fields["ticket_type"] = forms.ChoiceField(
                    choices=TicketType.choices,
                    disabled=True,
                )
        for field in fields_to_remove:
            del self.fields[field]

    class Meta:
        model = User
        fields = (
            "name",
            "github_username",
            "slack_member_id",
            "gender",
            "profession",
            "company",
            "ticket_type",
        )


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
