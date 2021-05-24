from abc import ABC, abstractmethod
from typing import Optional


class EmailClient(ABC):
    # account
    @abstractmethod
    def send_signup_email(self, to_email: str, *, email_confirmation_url: str) -> None:
        pass

    @abstractmethod
    def send_reset_password_email(self, to_email: str, *, reset_password_url: str) -> None:
        pass

    # interviews
    @abstractmethod
    def send_interview_passed_email(
        self, to_email: str, to_name: str, *, payment_value: int, payment_due_date: str
    ) -> None:
        pass

    @abstractmethod
    def send_interview_failed_email(self, to_email: str, to_name: str, *, message: str) -> None:
        pass

    # payments
    @abstractmethod
    def send_payment_accepted_proof_email(self, to_email: str, to_name: str, *, message: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def send_payment_need_additional_proof_email(self, to_email: str, to_name: str, *, message: str) -> None:
        pass

    @abstractmethod
    def send_payment_refused_proof_email(self, to_email: str, to_name: str, *, message: str) -> None:
        pass

    # bulk emails
    # application is over
    @abstractmethod
    def send_application_is_over_passed(self, to_email: str, to_name: str) -> None:
        pass

    @abstractmethod
    def send_application_is_over_failed(self, to_email: str, to_name: str) -> None:
        pass

    # selected for payment
    @abstractmethod
    def send_selected_and_payment_details(
        self, to_email: str, to_name: str, *, payment_value: int, payment_due_date: str
    ) -> None:
        pass

    # select for interview
    @abstractmethod
    def send_selected_interview_details(self, to_email: str, to_name: str) -> None:
        pass

    # admissions are over
    @abstractmethod
    def send_admissions_are_over_not_selected(self, to_email: str, to_name: str) -> None:
        pass

    # from candidates to admin! "contact us" email
    @abstractmethod
    def send_contact_us_email(self, from_email: str, user_name: str, user_url: str, message: str) -> None:
        pass
