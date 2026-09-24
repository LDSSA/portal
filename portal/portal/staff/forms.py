from django import forms

from portal.users.models import AdmissionsMode


class AdmissionsModeForm(forms.Form):
    admissions_mode = forms.ChoiceField(
        choices=AdmissionsMode.choices, label="Admissions mode for new applicants"
    )
