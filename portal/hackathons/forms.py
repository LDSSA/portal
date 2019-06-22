import logging

from crispy_forms.layout import Field
from django import forms
from django.core.exceptions import ValidationError

from . import models


logger = logging.getLogger(__name__)


class CustomCheckbox(Field):
    template = 'crispy/custom_checkbox.html'


class StudentAttendanceForm(forms.ModelForm):
    class Meta:
        model = models.Attendance
        fields = ['will_attend', 'remote']

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.hackathon.status != 'taking_attendance':
            raise forms.ValidationError("Marking attendance is closed")
        return cleaned_data


class TeamForm(forms.ModelForm):
    class Meta:
        model = models.Team
        fields = ['name', 'logo']


class InstructorHackathonForm(forms.ModelForm):
    class Meta:
        model = models.Hackathon
        fields = [
            'status',
            'max_submissions',
            'team_size',
            'max_team_size',
            'max_teams',
            'descending',
            'scoring_fcn',
            'y_true',
        ]

    # def clean_teams_closed(self):
    #     if self.cleaned_data['teams_closed']:
    #         if not self.instance.teams.exists():
    #             # TODO not shown
    #             raise forms.ValidationError("Generate teams first",
    #                                         code='invalid')
    #         self.cleaned_data['attendance_open'] = False
