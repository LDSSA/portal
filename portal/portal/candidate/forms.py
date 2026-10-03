from django import forms

from portal.users.models import AcademyTypePreference


class CodeOfConductForm(forms.Form):
    accepted = forms.BooleanField(
        label="I have read and accept the code of conduct and refund policy. I understand that violating these terms can lead to expulsion without a refund."
    )


class ScholarshipForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("yes", "Yes"), ("no", "No")),
        widget=forms.RadioSelect,
        label="Do you want to apply for a scholarship?",
    )


class AcademyTypeForm(forms.Form):
    academy_type = forms.ChoiceField(
        choices=AcademyTypePreference.choices, label="Attendance preference"
    )


class DocumentUploadForm(forms.Form):
    file = forms.FileField()
