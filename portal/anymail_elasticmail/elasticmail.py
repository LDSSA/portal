import json
import logging

from anymail.backends.base_requests import (
    AnymailRequestsBackend,
    RequestsPayload,
)
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import ANYMAIL_STATUSES, AnymailRecipientStatus
from anymail.utils import get_anymail_setting

from config.settings.settings import ANYMAIL

logger = logging.getLogger(__name__)

V2_API_URL = "https://api.elasticemail.com/v2/"
V4_API_URL = "https://api.elasticemail.com/v4/"


class ElasticmailBackend(AnymailRequestsBackend):
    esp_name = "Elasticmail"

    def __init__(self, **kwargs):
        """Init options from Django settings"""
        esp_name = self.esp_name
        self.api_key = get_anymail_setting(
            "api_key", esp_name=esp_name, kwargs=kwargs, allow_bare=True
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
        # self.debug_api_requests = True

    def build_message_payload(self, message, defaults):
        return ElasticmailV4Payload(
            message,
            defaults,
            self,
            headers={
                "X-ElasticEmail-ApiKey": self.api_key,
            },
        )

    def parse_recipient_status(self, response, payload, message):
        try:
            parsed_response = self.deserialize_json_response(response, payload, message)
        except json.JSONDecodeError as exc:
            raise AnymailRequestsAPIError(
                "Invalid Elasticmail API response format",
                email_message=message,
                payload=payload,
                response=response,
                backend=self,
            ) from exc

        return {
            message.to[0]: AnymailRecipientStatus(
                message_id=parsed_response["MessageID"], status="sent"
            )
        }


class ElasticmailV4Payload(RequestsPayload):
    def get_api_endpoint(self):
        return "emails/transactional"

    def serialize_data(self):
        return self.serialize_json(self.data)

    def init_payload(self):
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
            "Options": {
                "TrackOpens": "true",
                "TrackClicks": "false",
            },
        }
        # self.files = []
        # self.headers = {}

    def set_from_email_list(self, emails):
        # If your backend supports multiple from emails, override this to handle the whole list;
        # otherwise just implement set_from_email
        if len(emails) > 1:
            self.unsupported_feature("multiple from emails")
            # fall through if ignoring unsupported features
        if len(emails) > 0:
            self.data["Content"]["From"] = emails[0].address

    def set_from_email(self, email):
        self.data["Content"]["From"] = email.address

    def add_recipient(self, recipient_type, email):
        type_map = {
            "to": "To",
            "cc": "CC",
            "bcc": "BCC",
        }
        self.data["Recipients"][type_map[recipient_type]].append(email.address)

    def set_subject(self, subject):
        self.data["Content"]["Subject"] = subject

    def set_reply_to(self, emails):
        if len(emails) > 0:
            self.data["Content"]["ReplyTo"] = emails[0].address
            if len(emails) > 1:
                self.unsupported_feature("Multiple reply_to addresses")

    def set_extra_headers(self, headers):
        # headers is a CaseInsensitiveDict, and is a copy (so is safe to modify)
        self.unsupported_feature("extra_headers")

    def set_text_body(self, body):
        self.data["Content"]["Merge"].update({"message": body})
        # self.data["Content"]["Body"].append(
        #     {
        #         "ContentType": "PlainText",
        #         "Content": body,
        #         "Charset": "utf-8",
        #     }
        # )

    def set_html_body(self, body):
        self.data["Content"]["Merge"].update({"message": body})
        # self.data["Content"]["Body"].append(
        #     {
        #         "ContentType": "HTML",
        #         "Content": body,
        #         "Charset": "utf-8",
        #     }
        # )

    def add_alternative(self, content, mimetype):
        if mimetype == "text/plain":
            self.set_txt_body(content)
        else:
            self.unsupported_feature("alternative part with type '%s'" % mimetype)

    def add_attachment(self, attachment):
        pass

    def set_template_id(self, template_id):
        self.data["Content"]["TemplateName"] = template_id

    def set_metadata(self, metadata):
        self.data["Content"]["Merge"].update(metadata)

    def set_track_clicks(self, track_clicks):
        self.data["Options"]["TrackClicks"] = "true" if track_clicks else "false"

    def set_track_opens(self, track_opens):
        self.data["Options"]["TrackOpens"] = "true" if track_opens else "false"


class ElasticmailV2Payload(RequestsPayload):
    def get_api_endpoint(self):
        return "/emails/send"

    def serialize_data(self):
        return self.serialize_json(self.data)

    # def get_request_params(self, api_url):
    #     params = super().get_request_params(api_url)
    #     params['headers']['X-ElasticEmail-ApiKey'] = self.api

    def init_payload(self):
        self.data = {}
        self.files = []
        # self.headers = {}

    def set_from_email_list(self, emails):
        # If your backend supports multiple from emails, override this to handle the whole list;
        # otherwise just implement set_from_email
        if len(emails) > 1:
            self.unsupported_feature("multiple from emails")
            # fall through if ignoring unsupported features
        if len(emails) > 0:
            self.params["from"] = emails[0].address

    def set_from_email(self, email):
        self.params["from"] = email.address

    def add_recipient(self, recipient_type, email):
        type_map = {
            "to": "msgTo",
            "cc": "msgCC",
            "BCC": "msgBcc",
        }
        self.params[type_map[recipient_type]] = email.address

    def set_subject(self, subject):
        self.params["subject"] = subject

    def set_reply_to(self, emails):
        if len(emails) > 0:
            self.params["replyTo"] = emails[0].address
            if len(emails) > 1:
                self.unsupported_feature("Multiple reply_to addresses")

    def set_extra_headers(self, headers):
        # headers is a CaseInsensitiveDict, and is a copy (so is safe to modify)
        self.unsupported_feature("extra_headers")

    def set_text_body(self, body):
        self.params["bodyText"] = body

    def set_html_body(self, body):
        self.params["bodyHtml"] = body

    def add_alternative(self, content, mimetype):
        if mimetype == "text/plain":
            self.set_txt_body(content)
        else:
            self.unsupported_feature("alternative part with type '%s'" % mimetype)

    def add_attachment(self, attachment):
        pass

    def set_template_id(self, template_id):
        self.params["template"] = template_id

    def set_metadata(self, metadata):
        self.params.update({f"merge_{k}": v for k, v in metadata.items()})

    def set_track_clicks(self, track_clicks):
        self.params["trackClicks"] = "true" if track_clicks else "false"

    def set_track_opens(self, track_opens):
        self.params["trackOpens"] = "true" if track_opens else "false"
