from django.core.mail.backends.smtp import EmailBackend


class PortalEmailBackend(EmailBackend):
    def _send(self, email_message):
        if hasattr(email_message, "template_id"):
            email_message.body = email_message.body + f"\n{email_message.template_id}"
            email_message.body = email_message.body + f"\n{email_message.metadata}"
        return super()._send(email_message)
