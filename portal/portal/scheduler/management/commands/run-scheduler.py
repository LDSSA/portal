import logging
from time import sleep

from constance import config
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from portal.selection.notifications import deliver_pending_emails

logger = logging.getLogger(__name__)


def update_portal_status():
    """Advance the exam calendar even while new signups use no-exam admissions."""
    now = timezone.now()
    if now >= config.ACADEMY_START:
        status = "academy"
    elif now >= config.ADMISSIONS_SELECTION_START:
        status = "admissions:selection"
    elif now >= config.ADMISSIONS_APPLICATIONS_START:
        status = "admissions:applications"
    else:
        status = "admissions"
    if config.PORTAL_STATUS != status:
        config.PORTAL_STATUS = status
    # The signup adapter applies the exam deadline. Never overwrite the master
    # signup flag: doing so would also close no-exam registrations.


def refresh_certificates():
    from portal.academy.services import refresh_certificate_eligibility
    from portal.users.models import User

    for user in User.objects.filter(is_student=True).iterator():
        refresh_certificate_eligibility(user)


class Command(BaseCommand):
    help = "Run the exam calendar scheduler and enrollment email worker"

    def handle(self, *args, **options):
        cycles = 0
        while True:
            for operation in (update_portal_status, deliver_pending_emails):
                try:
                    operation()
                except Exception:
                    logger.exception(
                        "Scheduler operation failed: %s", operation.__name__
                    )
                finally:
                    close_old_connections()
            if cycles % 360 == 0:
                try:
                    refresh_certificates()
                except Exception:
                    logger.exception("Certificate refresh failed")
                finally:
                    close_old_connections()
            cycles += 1
            sleep(10)
