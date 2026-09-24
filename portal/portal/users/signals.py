from allauth.account.signals import email_confirmed
from django.dispatch import receiver

from portal.selection.enrollment import complete_registration


@receiver(email_confirmed)
def complete_verified_registration(sender, request, email_address, **kwargs):
    complete_registration(email_address.user)
