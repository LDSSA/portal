from django import forms  # noqa: D100

from portal.capstone import models


class ApiForm(forms.ModelForm):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.StudentApi
        fields = ["url"]  # noqa: RUF012


class ReportForm(forms.ModelForm):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.Report
        fields = ["file"]  # noqa: RUF012
