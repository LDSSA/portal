from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.html import format_html


def send_signup_email(to_email, email_confirmation_url):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        subject="Action needed: Confirm your email address",
    )
    email.template_id = "Admissions - generic message"
    email.body = format_html(
        "Welcome to the Lisbon Data Science Starters Academy admissions portal.<br>"
        'Please <a href="{}">confirm your email address</a>, then return to the portal '
        "to complete your registration. Replying to this email does not verify your account.",
        email_confirmation_url,
    )
    email.send()


def send_reset_password_email(to_email, reset_password_url):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        subject="Reset your Password on the LDSSA Admissions Portal",
    )
    email.template_id = "Admissions - forgot password"
    email.metadata = {"reset_password_url": reset_password_url}
    email.send()


def send_application_is_over_passed(to_email, to_name):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Keep your fingers crossed!",
    )
    email.template_id = "Admissions - passed admission tests"
    email.metadata = {"to_name": to_name}
    email.send()


def send_application_is_over_failed(to_email, to_name):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Sorry! You did not pass the LDSSA admissions tests.",
    )
    email.template_id = "Admissions - failed admission tests"
    email.metadata = {"to_name": to_name}
    email.send()


def send_admissions_are_over_not_selected(to_email, to_name):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Sorry! Try again next year",
    )
    email.template_id = "Admissions - over not selected"
    email.metadata = {"to_name": to_name}
    email.send()


def send_selected_and_payment_details(
    to_email,
    to_name,
    *,
    payment_value: int,
    payment_due_date: str,
):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Complete your LDSSA enrollment",
    )
    email.template_id = "Admissions - generic message"
    email.body = format_html(
        "Hello {},<br>You have been selected after the admission tests. "
        "Please pay €{} and submit your payment documents by {}. "
        '<a href="{}">Open the portal</a> for bank details and document submission. '
        "A student-rate ticket also requires a student ID.",
        to_name,
        payment_value,
        payment_due_date,
        settings.BASE_URL,
    )
    email.send()


def send_payment_accepted_proof_email(to_email: str, to_name: str, *, message: str):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="You're IN!",
    )
    email.template_id = "Admissions - payment accepted"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_payment_need_additional_proof_email(
    to_email: str, to_name: str, *, message: str
):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="You're ALMOST IN!",
    )
    email.template_id = "Admissions - payment need additional proof"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_payment_refused_proof_email(to_email, to_name, *, message):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Oh no! There was something wrong here...",
    )
    email.template_id = "Admissions - payment refused"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_interview_passed_email(
    to_email,
    to_name,
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


def send_interview_failed_email(to_email: str, to_name: str, *, message: str):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="Update on your LDSSA scholarship interview",
    )
    email.template_id = "Admissions - interview failed"
    email.metadata = {"to_name": to_name, "message": message}
    email.send()


def send_selected_interview_details(to_email, to_name):
    email = EmailMessage(
        to=[to_email],
        bcc=["admissions@lisbondatascience.org"],
        from_email=settings.ADMISSIONS_FROM_EMAIL,
        subject="LDSSA scholarship interview details",
    )
    email.template_id = "Admissions - generic message"
    email.body = format_html(
        "Hello {},<br>You have been selected for a scholarship interview. "
        "Staff will contact you to arrange a time. Please wait for the decision before paying. "
        "If the scholarship is refused, your admission ends; it cannot be converted to a full-fee application.",
        to_name,
    )
    email.send()


def send_contact_us_email(from_email, user_name, user_url, message):
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
