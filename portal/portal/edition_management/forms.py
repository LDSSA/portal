from django import forms

from .planner import organizers, protected_ids


class PrepareForm(forms.Form):
    retained = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label="Organizers to keep",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["retained"].queryset = organizers().exclude(
            pk__in=protected_ids(actor)
        )
        self.fields["retained"].initial = list(
            self.fields["retained"].queryset.values_list("pk", flat=True)
        )


class ConfirmForm(forms.Form):
    backup_first = forms.BooleanField(
        required=False, initial=True, label="Back up before reset"
    )
    reviewed = forms.BooleanField(
        label="I have reviewed all accounts listed for deletion, including unverified/recent registrations, and confirm they may be deleted."
    )
    confirmed = forms.BooleanField(
        label="I confirm the reset of this environment. This cannot be undone without restoring a backup."
    )
