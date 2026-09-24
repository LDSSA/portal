"""Deliver the enrollment outbox, retrying provider failures without losing decisions."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape

from .models import EnrollmentEmail

logger = logging.getLogger(__name__)


def deliver_pending_emails(limit=50):
    sent = 0
    for _ in range(limit):
        with transaction.atomic():
            item = (
                EnrollmentEmail.objects.select_for_update(skip_locked=True)
                .filter(sent_at__isnull=True, next_attempt_at__lte=timezone.now())
                .order_by("created_at")
                .first()
            )
            if item is None:
                break
            item.attempts += 1
            email = EmailMessage(
                subject=item.subject,
                body=str(escape(item.body)).replace("\n", "<br>"),
                from_email=settings.ADMISSIONS_FROM_EMAIL,
                to=[item.recipient],
                bcc=["admissions@lisbondatascience.org"],
            )
            email.template_id = "Admissions - generic message"
            try:
                if email.send() != 1:
                    raise RuntimeError("Email provider did not accept the message.")
            except Exception as exc:
                logger.exception("Enrollment email %s could not be sent", item.pk)
                item.last_error = str(exc)
                item.next_attempt_at = timezone.now() + timedelta(
                    seconds=min(3600, 30 * 2 ** min(item.attempts, 7))
                )
            else:
                item.sent_at = timezone.now()
                item.last_error = ""
                sent += 1
            item.save(
                update_fields=["attempts", "sent_at", "last_error", "next_attempt_at"]
            )
    return sent
