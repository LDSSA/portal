import json  # noqa: D100
import logging

from anymail.backends.base_requests import (
    AnymailRequestsBackend,
    RequestsPayload,
)
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailRecipientStatus
from anymail.utils import get_anymail_setting

logger = logging.getLogger(__name__)

V2_API_URL = "https://api.elasticemail.com/v2/"
V4_API_URL = "https://api.elasticemail.com/v4/"


class ElasticmailBackend(AnymailRequestsBackend):  # noqa: D101
    esp_name = "Elasticmail"

    def __init__(self, **kwargs) -> None:  # noqa: ANN003, ANN101
        """Init options from Django settings."""
        esp_name = self.esp_name
        self.api_key = get_anymail_setting(
            "api_key",
            esp_name=esp_name,
            kwargs=kwargs,
            allow_bare=True,
        )
        api_url = get_anymail_setting(
            "api_url",
            esp_name=esp_name,
            kwargs=kwargs,
            default=V4_API_URL,
        )
        if not api_url.endswith("/"):
            api_url += "/"
        super().__init__(api_url, **kwargs)
        # self.debug_api_requests = True  # noqa: ERA001

    def build_message_payload(self, message, defaults):  # noqa: ANN001, ANN101, ANN201, D102
        return ElasticmailV4Payload(
            message,
            defaults,
            self,
            headers={
                "X-ElasticEmail-ApiKey": self.api_key,
            },
        )

    def parse_recipient_status(  # noqa: ANN201, D102
        self, response, payload, message  # noqa: ANN001, ANN101
    ):  # noqa: ANN001, ANN101, ANN201, D102
        try:
            parsed_response = self.deserialize_json_response(response, payload, message)
        except json.JSONDecodeError as exc:
            msg = "Invalid Elasticmail API response format"
            raise AnymailRequestsAPIError(
                msg,
                email_message=message,
                payload=payload,
                response=response,
                backend=self,
            ) from exc

        return {
            message.to[0]: AnymailRecipientStatus(
                message_id=parsed_response["MessageID"],
                status="sent",
            ),
        }


class ElasticmailV4Payload(RequestsPayload):  # noqa: D101
    def get_api_endpoint(self):  # noqa: ANN101, ANN201, D102
        return "emails/transactional"

    def serialize_data(self):  # noqa: ANN101, ANN201, D102
        return self.serialize_json(self.data)

    def init_payload(self):  # noqa: ANN101, ANN201, D102
        self.data = {
            "Recipients": {
                "To": [],
                "CC": [],
                "BCC": [],
            },
            "Content": {
                "Body": [],
                "Merge": {},
                "TemplateName": "Admissions - generic message",
            },
        }

    def set_from_email_list(self, emails):  # noqa: ANN001, ANN101, ANN201, D102
        # If your backend supports multiple from emails, override this to handle the whole list;
        # otherwise just implement set_from_email
        if len(emails) > 1:
            self.unsupported_feature("multiple from emails")
            # fall through if ignoring unsupported features
        if len(emails) > 0:
            self.data["Content"]["From"] = emails[0].address

    def set_from_email(self, email):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["From"] = email.address

    def add_recipient(self, recipient_type, email):  # noqa: ANN001, ANN101, ANN201, D102
        type_map = {
            "to": "To",
            "cc": "CC",
            "bcc": "BCC",
        }
        self.data["Recipients"][type_map[recipient_type]].append(email.address)

    def set_subject(self, subject):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["Subject"] = subject

    def set_reply_to(self, emails):  # noqa: ANN001, ANN101, ANN201, D102
        if len(emails) > 0:
            self.data["Content"]["ReplyTo"] = emails[0].address
            if len(emails) > 1:
                self.unsupported_feature("Multiple reply_to addresses")

    def set_extra_headers(self, headers):  # noqa: ANN001, ANN101, ANN201, ARG002, D102
        # headers is a CaseInsensitiveDict, and is a copy (so is safe to modify)
        self.unsupported_feature("extra_headers")

    def set_text_body(self, body):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["Merge"].update({"message": body})

    def set_html_body(self, body):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["Merge"].update({"message": body})

    def add_alternative(self, content, mimetype):  # noqa: ANN001, ANN101, ANN201, D102
        if mimetype == "text/plain":
            self.set_txt_body(content)
        else:
            self.unsupported_feature("alternative part with type '%s'" % mimetype)

    def add_attachment(self, attachment):  # noqa: ANN001, ANN101, ANN201, D102
        pass

    def set_template_id(self, template_id):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["TemplateName"] = template_id

    def set_metadata(self, metadata):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Content"]["Merge"].update(metadata)

    def set_track_clicks(self, track_clicks):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Options"]["TrackClicks"] = "true" if track_clicks else "false"

    def set_track_opens(self, track_opens):  # noqa: ANN001, ANN101, ANN201, D102
        self.data["Options"]["TrackOpens"] = "true" if track_opens else "false"
