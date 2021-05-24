import logging
from typing import Any, Optional, Dict

from django.core.mail import send_mail

from .elastic import ElasticEmailClient

logger = logging.getLogger(__name__)

ELASTIC_EMAIL_URL = ""


class LocalEmailClient(ElasticEmailClient):
    def _send_email(
        self, receiver: str, template_id: int, subject: str, *, merge: Optional[Dict[str, Any]] = None
    ) -> None:
        data = {
            "apikey": self.api_key,
            "from": self.sender,
            "subject": subject,
            "msgTo": receiver,
            "msgBcc": self.sender,
            "template": template_id,
        }

        if merge is not None:
            data = {**data, **{f"merge_{k}": v for k, v in merge.items()}}

        send_mail(data["subject"], str(data), data['from'], data['msgTo'])

        logger.info(f"email sent: template_id={template_id}, to_email={receiver}")
