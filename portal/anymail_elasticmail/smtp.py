from django.core.mail.backends.smtp import EmailBackend  # noqa: D100


class PortalEmailBackend(EmailBackend):  # noqa: D101
    def _send(self, email_message):  # noqa: ANN001, ANN101, ANN202
        if hasattr(email_message, "template_id"):
            email_message.body = email_message.body + f"\n{email_message.template_id}"
            email_message.body = email_message.body + f"\n{email_message.metadata}"
        return super()._send(email_message)
