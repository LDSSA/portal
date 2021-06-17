import logging
from time import sleep

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.utils import timezone
from constance import config


# from portal.capstone.simulator import run
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run scheduler"

    def handle(self, *args, **options):
        scheduled_fcns = (update_portal_status,)

        while True:
            logger.info("Running scheduler...")

            for fcn in scheduled_fcns:
                try:
                    fcn()
                except Exception:
                    logger.exception(f"Exception in {fcn.__name__}")

            # Close connection after each run
            # https://code.djangoproject.com/ticket/21596#comment:29
            # https://docs.djangoproject.com/en/1.0/ref/databases/
            connection.close()
            logger.info("Scheduler done...")

            # chill
            sleep(10)


def update_portal_status():
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

    elif config.PORTAL_STATUS == "admissions:selection":
        if dt >= config.ACADEMY_START:
            config.PORTAL_STATUS = "academy"
