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
            'name',
            'logo',
            'github_username',
            'slack_member_id',
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
