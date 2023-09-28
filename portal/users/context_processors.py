import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def login_view(request):
    logging.info(settings.LOGIN_URL)
    return {"LOGIN_VIEW": settings.LOGIN_URL}
