import logging  # noqa: D100

from django.conf import settings

logger = logging.getLogger(__name__)


def login_view(request):  # noqa: ANN001, ANN201, ARG001, D103
    logging.info(settings.LOGIN_URL)
    return {"LOGIN_VIEW": settings.LOGIN_URL}
