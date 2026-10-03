from constance.forms import ConstanceForm
from django import forms


class AdmissionsConfigForm(ConstanceForm):
    def clean(self):
        data = super().clean()
        if data.get("ADMISSIONS_PAYMENT_DAYS", 1) < 1:
            self.add_error("ADMISSIONS_PAYMENT_DAYS", "Payment days must be positive.")
        duration = data.get("ADMISSIONS_CODING_TEST_DURATION")
        if duration is not None and duration.total_seconds() <= 0:
            self.add_error(
                "ADMISSIONS_CODING_TEST_DURATION", "Duration must be positive."
            )
        if data.get("NO_EXAM_USE_SCHEDULE"):
            pairs = (
                ("NO_EXAM_SIGNUPS_START", "NO_EXAM_SIGNUPS_END", False),
                ("NO_EXAM_SIGNUPS_END", "NO_EXAM_REGISTRATION_END", True),
                ("NO_EXAM_PAYMENTS_START", "NO_EXAM_PAYMENTS_END", False),
                ("NO_EXAM_REGISTRATION_END", "NO_EXAM_PAYMENTS_END", True),
            )
            for start, end, equal in pairs:
                a, b = data.get(start), data.get(end)
                if a is not None and b is not None and (a > b if equal else a >= b):
                    self.add_error(
                        end,
                        f"Must be after {start}"
                        + (" or equal to it." if equal else "."),
                    )
        if data.get("ADMISSIONS_MODE") == "exam":
            start, end = data.get("ADMISSIONS_APPLICATIONS_START"), data.get(
                "ADMISSIONS_SELECTION_START"
            )
            if start is not None and end is not None and start >= end:
                raise forms.ValidationError(
                    "The exam opening must precede the selection start."
                )
        return data
