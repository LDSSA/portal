from django.conf import settings  # noqa: D100
from django.core.mail import EmailMessage


def send_signup_email(to_email, email_confirmation_url):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        subject="Action needed: Confirm your email address",
    )
    email.template_id = "Admissions - confirm email"
    email.metadata = {"email_confirmation_url": email_confirmation_url}
    email.send()


def send_reset_password_email(to_email, reset_password_url):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        subject="Reset your Password on the LDSSA Admissions Portal",
    )
    email.template_id = "Admissions - forgot password"
    email.metadata = {"reset_password_url": reset_password_url}
    email.send()


def send_application_is_over_passed(to_email, to_name):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Keep your fingers crossed!",
    )
    email.template_id = "Admissions - passed admission tests"
    email.metadata = {"to_name": to_name}
    email.send()


def send_application_is_over_failed(to_email, to_name):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Sorry! Try again next year",
    )
    email.template_id = "Admissions - failed admission tests"
    email.metadatae = {"to_name": to_name}
    email.send()


def send_admissions_are_over_not_selected(to_email, to_name):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Sorry! Try again next year",
    )
    email.template_id = "Admissions - over not selected"
    email.metadata = {"to_name": to_name}
    email.send()


def send_selected_and_payment_details(  # noqa: ANN201, D103
    to_email,  # noqa: ANN001
    to_name,  # noqa: ANN001
    *,
    payment_value: int,
    payment_due_date: str,
):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="You're ALMOST IN!",
    )
    email.template_id = "Admissions - selected and payment details"
    email.metadata = {
        "to_name": to_name,
        "payment_value": payment_value,
        "payment_due_date": payment_due_date,
    }
    email.send()


def send_payment_accepted_proof_email(  # noqa: ANN201, D103
    to_email: str, to_name: str, *, message: str
):  # noqa: ANN201, ARG001, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="You're IN!",
    )
    email.template_id = "Admissions - payment accepted"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_payment_need_additional_proof_email(  # noqa: ANN201, D103
    to_email: str, to_name: str, *, message: str
):  # noqa: ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="You're ALMOST IN!",
    )
    email.template_id = "Admissions - payment need additional proof"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_payment_refused_proof_email(to_email, to_name, *, message):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Oh no! There was something wrong here...",
    )
    email.template_id = "Admissions - payment refused"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_interview_passed_email(  # noqa: ANN201, D103
    to_email,  # noqa: ANN001
    to_name,  # noqa: ANN001
    *,
    payment_value: int,
    payment_due_date: str,
):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="The results are out - You've made it!",
    )
    email.template_id = "Admissions - interview passed and payment details"
    email.metadata = {
        "to_name": to_name,
        "payment_value": payment_value,
        "payment_due_date": payment_due_date,
    }
    email.send()


def send_interview_failed_email(to_email: str, to_name: str, *, message: str):  # noqa: ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Update on your LDSSA scholarship interview",
    )
    email.template_id = "Admissions - interview failed"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_selected_interview_details(to_email, to_name):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="LDSSA scholarship interview details",
    )
    email.template_id = "Admissions - selected interview details"
    email.metadata = {"to_name": to_name}
    email.send()


def send_contact_us_email(from_email, user_name, user_url, message):  # noqa: ANN001, ANN201, D103
    email = EmailMessage(
        to=["admissions@lisbondatascience.org"],
        reply_to=[from_email],
        subject=f"[Admissions Portal] Support request from {from_email}",
    )
    email.template_id = "Admissions - contact us"
    email.metadata = {
        "from_email": from_email,
        "user_name": user_name,
        "user_url": user_url,
        "message": message,
    }
    email.send()
