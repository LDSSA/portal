# from allauth.account.forms import SignupForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.core.exceptions import ValidationError
import django.forms as forms
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class UserChangeForm(forms.ModelForm):
    name = forms.CharField()
    logo = forms.CharField()
    github_username = forms.CharField()
    slack_member_id = forms.CharField()

    class Meta:
        model = User
        fields = (
            "name",
            "logo",
            "github_username",
            "slack_member_id",
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
        if settings.ENABLE_ADMISSIONS:
            self.fields["gender"] = forms.ChoiceField(choices=User.GENDERS)
            self.fields["profession"] = forms.CharField(max_length=50)
            self.fields["company"] = forms.CharField(max_length=100)

    def signup(self, request, user):
        user.name = self.cleaned_data['name']
        if settings.ENABLE_ADMISSIONS:
            user.gender = self.cleaned_data['gender']
            user.profession = self.cleaned_data['profession']
            user.company = self.cleaned_data['company']
        user.save()
