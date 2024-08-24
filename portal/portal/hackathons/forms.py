import logging

from crispy_forms.layout import Field
from django import forms

from . import models

logger = logging.getLogger(__name__)


class CustomCheckbox(Field):
    template = "crispy/custom_checkbox.html"


class StudentAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.Attendance
        fields = [
            # 'remote'
        ]

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.hackathon.status != "taking_attendance":
            msg = "Marking attendance is closed"
            raise forms.ValidationError(msg)
        return cleaned_data


class TeamForm(forms.ModelForm):
    class Meta:
        model = models.Team
        fields = ["name", "logo"]


class SubmitForm(forms.Form):
    data = forms.FileField()

    class Meta:
        fields = ["data"]


class InstructorHackathonForm(forms.ModelForm):
    class Meta:
        model = models.Hackathon
        fields = [
            "status",
            "max_submissions",
            "team_size",
            "max_team_size",
            "max_teams",
            "descending",
            "script_file",
            "data_file",
        ]

    # def clean_teams_closed(self):
    #     if self.cleaned_data['teams_closed']:
    #         if not self.instance.teams.exists():
    #             # TODO: not shown
    #             raise forms.ValidationError("Generate teams first",
    #                                         code='invalid')
    #         self.cleaned_data['attendance_open'] = False
