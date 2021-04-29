from typing import Optional

from django.conf import settings

# TODO TODO replace interface, create issues
from email_client import ElasticEmailClient, EmailClient, LocalEmailClient
from feature_flags_client import (
    DBFeatureFlagsClient,
    FeatureFlagsClient,
    MockFeatureFlagsClient,
)
from flags.domain import FlagsGetSet
from grader_client import (
    GraderClient,
    GraderClientFakeScores,
    GraderClientHttp,
)
from storage_client import (
    AWSS3StorageClient,
    LocalStorageClient,
    LocalStorageClientWithServer,
    StorageClient,
)


class InterfaceException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class _Interface:
    def __init__(self) -> None:
        self._storage_client: Optional[StorageClient] = None
        self._email_client: Optional[EmailClient] = None
        self._feature_flag_client: Optional[FeatureFlagsClient] = None
        self._grader_client: Optional[GraderClient] = None

    @staticmethod
    def new_storage_client(client_id: Optional[str] = None) -> StorageClient:
        client_id = client_id or settings.STORAGE_CLIENT
        if client_id == "S3":
            return AWSS3StorageClient(bucket_name=settings.STORAGE_BUCKET)
        elif client_id == "LOCAL":
            return LocalStorageClient(workspace=settings.STORAGE_LOCAL_DIR)
        elif client_id == "LOCALSERVER":
            return LocalStorageClientWithServer(
                workspace=settings.STORAGE_LOCAL_DIR
            )
        raise InterfaceException(
            msg=f"No StorageClient implementation for `{client_id}`"
        )

    @property
    def storage_client(self) -> StorageClient:
        if self._storage_client is None:
            self._storage_client = self.new_storage_client()
        return self._storage_client

    @staticmethod
    def new_email_client(client_id: Optional[str] = None) -> EmailClient:
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
    def email_client(self) -> EmailClient:
        if self._email_client is None:
            self._email_client = self.new_email_client()
        return self._email_client

    @staticmethod
    def new_feature_flag_client(
        client_id: Optional[str] = None,
    ) -> FeatureFlagsClient:
        client_id = client_id or settings.FF_CLIENT
        if client_id == "DB":
            return DBFeatureFlagsClient(FlagsGetSet())
        elif client_id == "MOCK":
            return MockFeatureFlagsClient()
        raise InterfaceException(
            msg=f"No FeatureFlagsClient implementation for `{client_id}`"
        )

    @property
    def feature_flag_client(self) -> FeatureFlagsClient:
        if self._feature_flag_client is None:
            self._feature_flag_client = self.new_feature_flag_client()
        return self._feature_flag_client

    @staticmethod
    def new_grader_client(client_id: Optional[str] = None) -> GraderClient:
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
    def grader_client(self) -> GraderClient:
        if self._grader_client is None:
            self._grader_client = self.new_grader_client()
        return self._grader_client


interface = _Interface()
