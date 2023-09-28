from django.core.mail.backends.smtp import EmailBackend  # noqa: D100


class PortalEmailBackend(EmailBackend):  # noqa: D101
    def _send(self, email_message):
        if hasattr(email_message, "template_id"):
            email_message.body = email_message.body + f"\n{getattr(email_message, 'template_id')}"
            email_message.body = email_message.body + f"\n{getattr(email_message, 'metadata')}"
        return super()._send(email_message)
