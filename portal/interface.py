from typing import Optional

from django.conf import settings

from portal.email_client import ElasticEmailClient, EmailClient, LocalEmailClient


class InterfaceException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class _Interface:
    def __init__(self) -> None:
        self._storage_client = None
        self._email_client = None
        self._feature_flag_client = None
        self._grader_client = None

    @staticmethod
    def new_storage_client(client_id: Optional[str] = None):
        return None

    @property
    def storage_client(self):
        if self._storage_client is None:
            self._storage_client = self.new_storage_client()
        return self._storage_client

    @staticmethod
    def new_email_client(client_id: Optional[str] = None):
        client_id = client_id or settings.EMAIL_CLIENT
        if client_id == "ELASTIC":
            return ElasticEmailClient(
                api_key=settings.ELASTIC_EMAIL_API_KEY,
                sender=settings.ELASTIC_EMAIL_SENDER,
            )
        elif client_id == "LOCAL":
            return LocalEmailClient(root=settings.EMAIL_LOCAL_DIR)
        raise InterfaceException(
            msg=f"No EmailClient implementation for `{client_id}`"
        )

    @property
    def email_client(self):
        if self._email_client is None:
            self._email_client = self.new_email_client()
        return self._email_client

    @property
    def feature_flag_client(self):
        if self._feature_flag_client is None:
            self._feature_flag_client = None
        return self._feature_flag_client

    @staticmethod
    def new_grader_client(client_id: Optional[str] = None):
        client_id = client_id or settings.GRADER_CLIENT
        if client_id == "HTTP":
            return GraderClientHttp(
                url=settings.GRADER_CLIENT_URL,
                auth_token=settings.GRADER_CLIENT_AUTH_TOKEN,
            )
        if client_id == "FAKE":
            return GraderClientFakeScores()
        raise InterfaceException(
            msg=f"No GraderClient implementation for `{client_id}`"
        )

    @property
    def grader_client(self):
        if self._grader_client is None:
            self._grader_client = self.new_grader_client()
        return self._grader_client


interface = _Interface()
