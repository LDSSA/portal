"""Module contains the context processors for the users app."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def login_view(request):
    """Add the login view to the context."""
    logging.info(settings.LOGIN_URL)
    return {"LOGIN_VIEW": settings.LOGIN_URL}
