import logging  # noqa: D100, N999
from time import sleep

from constance import config
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

# from portal.capstone.simulator import run  # noqa: ERA001
logger = logging.getLogger(__name__)


class Command(BaseCommand):  # noqa: D101
    help = "Run scheduler"  # noqa: A003

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        scheduled_fcns = (update_portal_status,)

        while True:
            logger.info("Running scheduler...")

            try:
                for fcn in scheduled_fcns:
                    fcn()
            except Exception:
                logger.exception("Exception in %s", fcn.__name__)

            # Close connection after each run
            # https://code.djangoproject.com/ticket/21596#comment:29
            # https://docs.djangoproject.com/en/1.0/ref/databases/
            connection.close()
            logger.info("Scheduler done...")

            # chill
            sleep(10)


def update_portal_status():  # noqa: ANN201, D103
    dt = timezone.now()

    # Initial portal state
    if config.PORTAL_STATUS == "admissions":
        if dt >= config.ADMISSIONS_APPLICATIONS_START:
            # Application phase starts, applicants can start making submissions
            logger.info("Opening applications...")

            config.PORTAL_STATUS = "admissions:applications"

    elif config.PORTAL_STATUS == "admissions:applications":
        if dt >= config.ADMISSIONS_SELECTION_START:
            # Selection phase starts, applicants can not longer make submissions
            logger.info("Closing candidate applications...")
            logger.info("Opening candidate selection...")

            config.PORTAL_STATUS = "admissions:selection"
            # Disable sign ups
            config.ACCOUNT_ALLOW_REGISTRATION = False

    elif config.PORTAL_STATUS == "admissions:selection" and dt >= config.ACADEMY_START:
        config.PORTAL_STATUS = "academy"
