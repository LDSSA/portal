import logging
# from allauth.account.forms import SignupForm

import django.forms as forms

# from allauth.account.forms import SignupForm
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from portal.users.models import Gender, TicketType, TicketTypeSelectable

User = get_user_model()
logger = logging.getLogger(__name__)


class UserChangeForm(forms.ModelForm):
    name = forms.CharField()

    def __init__(self, *args, **kwawgs):
        super().__init__(*args, **kwawgs)
        if config.PORTAL_STATUS == "academy":
            self.fields["logo"] = forms.CharField()
            self.fields["github_username"] = forms.CharField()
            self.fields["slack_member_id"] = forms.CharField()
        if config.PORTAL_STATUS not in (
            "admissions",
            "admissions:applications",
        ):
            self.fields["ticket_type"] = forms.ChoiceField(
                choices=TicketType.choices, disabled=True
            )
        else:
            self.fields["ticket_type"] = forms.ChoiceField(
                choices=TicketTypeSelectable.choices
            )

    class Meta:
        model = User
        fields = (
            "name",
            "gender",
            "profession",
            "company",
            "ticket_type",
        )


class UserCreationForm(auth.forms.UserCreationForm):

    error_message = auth.forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(auth.forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


class PortalSignupForm(forms.Form):
    name = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # del self.fields["username"].widget.attrs["autofocus"]
        self.fields["gender"] = forms.ChoiceField(choices=Gender.choices)
        self.fields["ticket_type"] = forms.ChoiceField(
            choices=TicketTypeSelectable.choices
        )
        self.fields["profession"] = forms.CharField(
            max_length=50, required=False
        )
        self.fields["company"] = forms.CharField(
            max_length=100, required=False
        )

    def signup(self, request, user):
        user.name = self.cleaned_data["name"]
        user.gender = self.cleaned_data["gender"]
        user.ticket_type = self.cleaned_data["ticket_type"]
        user.profession = self.cleaned_data["profession"]
        user.company = self.cleaned_data["company"]
        user.save()