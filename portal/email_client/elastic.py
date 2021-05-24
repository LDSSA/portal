from logging import getLogger
from typing import Any, Dict, Optional

import requests

from .client import EmailClient

logger = getLogger(__name__)


ELASTIC_EMAIL_URL = "https://api.elasticemail.com/v2/"


class ElasticEmailException(Exception):
    pass


class ElasticEmailClient(EmailClient):
    def __init__(self, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.url = ELASTIC_EMAIL_URL
        self.sender = sender  # sender email address

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

        resp = requests.post(f"{self.url}/email/send", data=data)

        if not resp.ok:
            logger.error(
                f"email not sent, response not ok: "
                f"template_id={template_id}, to_email={receiver}, status_code={resp.status_code}"
            )
            return
        resp_json = resp.json()
        if not resp_json["success"]:
            logger.error(
                f"email not sent, response error: "
                f"template_id={template_id}, to_email={receiver}, error={resp_json['error']}"
            )
            return

        logger.info(f"email sent: template_id={template_id}, to_email={receiver}")

    def send_signup_email(self, to_email: str, *, email_confirmation_url: str) -> None:
        subject = "Action needed: Confirm your email address"
        template_id = 2034
        merge = {"email_confirmation_url": email_confirmation_url}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_reset_password_email(self, to_email: str, *, reset_password_url: str) -> None:
        subject = "Reset your Password on the LDSSA Admissions Portal"
        template_id = 2654
        merge = {"reset_password_url": reset_password_url}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_application_is_over_passed(self, to_email: str, to_name: str) -> None:
        subject = "Keep your fingers crossed!"
        template_id = 2687
        merge = {"to_name": to_name}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_application_is_over_failed(self, to_email: str, to_name: str) -> None:
        subject = "Sorry! Try again next year"
        template_id = 2745
        merge = {"to_name": to_name}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_admissions_are_over_not_selected(self, to_email: str, to_name: str) -> None:
        subject = "Sorry! Try again next year"
        template_id = 2867
        merge = {"to_name": to_name}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_selected_and_payment_details(
        self, to_email: str, to_name: str, *, payment_value: int, payment_due_date: str
    ) -> None:
        subject = "You’re ALMOST IN!"
        template_id = 2891
        merge = {"to_name": to_name, "payment_value": payment_value, "payment_due_date": payment_due_date}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_payment_accepted_proof_email(self, to_email: str, to_name: str, *, message: Optional[str] = None) -> None:
        subject = "You’re IN!"
        template_id = 2964
        merge = {"to_name": to_name}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_payment_need_additional_proof_email(self, to_email: str, to_name: str, *, message: str) -> None:
        subject = "You’re ALMOST IN!"
        template_id = 3019
        merge = {"to_name": to_name, "message": message}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_payment_refused_proof_email(self, to_email: str, to_name: str, *, message: str) -> None:
        subject = "Oh no! There was something wrong here..."
        template_id = 3045
        merge = {"to_name": to_name, "message": message}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_interview_passed_email(
        self, to_email: str, to_name: str, *, payment_value: int, payment_due_date: str
    ) -> None:
        subject = "The results are out - You’ve made it!"
        template_id = 3766
        merge = {"to_name": to_name, "payment_value": payment_value, "payment_due_date": payment_due_date}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_interview_failed_email(self, to_email: str, to_name: str, *, message: str) -> None:
        subject = "Update on your LDSSA scholarship interview"
        template_id = 3767
        merge = {"to_name": to_name, "message": message}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_selected_interview_details(self, to_email: str, to_name: str) -> None:
        subject = "LDSSA scholarship interview details"
        template_id = 3765
        merge = {"to_name": to_name}
        self._send_email(to_email, template_id, subject, merge=merge)

    def send_contact_us_email(self, from_email: str, user_name: str, user_url: str, message: str) -> None:
        subject = f"[Admissions Portal] Support request from {from_email}"
        template_id = 7470
        merge = {"from_email": from_email, "user_name": user_name, "user_url": user_url, "message": message}
        self._send_email(self.sender, template_id, subject, merge=merge)
