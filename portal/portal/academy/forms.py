from django import forms

from .models import Grade


class GradeAdminForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if {"deadline_valid_override", "deadline_override_reason"} & set(
            self.changed_data
        ):
            if not data.get("deadline_override_reason", "").strip():
                self.add_error(
                    "deadline_override_reason",
                    "Explain why you are changing deadline validity.",
                )
        return data
