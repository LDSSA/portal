import logging  # noqa: D100

from crispy_forms.layout import Field
from django import forms

from . import models

logger = logging.getLogger(__name__)


class CustomCheckbox(Field):  # noqa: D101
    template = "crispy/custom_checkbox.html"


class StudentAttendanceForm(forms.ModelForm):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.Attendance
        fields = [  # noqa: RUF012
            # 'remote'
        ]

    def clean(self):  # noqa: ANN101, ANN201, D102
        cleaned_data = super().clean()
        if self.instance.hackathon.status != "taking_attendance":
            msg = "Marking attendance is closed"
            raise forms.ValidationError(msg)
        return cleaned_data


class TeamForm(forms.ModelForm):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.Team
        fields = ["name", "logo"]  # noqa: RUF012


class SubmitForm(forms.Form):  # noqa: D101
    data = forms.FileField()

    class Meta:  # noqa: D106
        fields = ["data"]  # noqa: RUF012


class InstructorHackathonForm(forms.ModelForm):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.Hackathon
        fields = [  # noqa: RUF012
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
    #             # TODO: not shown  # noqa: FIX002, TD002, TD003
    #             raise forms.ValidationError("Generate teams first",
    #                                         code='invalid')
    #         self.cleaned_data['attendance_open'] = False  # noqa: ERA001
