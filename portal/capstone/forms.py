from django import forms

from portal.capstone import models


class ApiForm(forms.ModelForm):
    class Meta:
        model = models.StudentApi
        fields = ["url"]


class ReportForm(forms.ModelForm):
    class Meta:
        model = models.Report
        fields = ["file"]
