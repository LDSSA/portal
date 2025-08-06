import logging
from time import sleep

from constance import config
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

# from portal.capstone.simulator import run
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run scheduler"

    def handle(self, *args, **options):
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


def update_portal_status():
    dt = timezone.now()

    # Initial portal state
    if dt >= config.ADMISSIONS_APPLICATIONS_START and dt < config.ADMISSIONS_SELECTION_START:
        # Application phase starts, applicants can start making submissions
        logger.info("Setting portal status to applications...")

        config.PORTAL_STATUS = "admissions:applications"
        # Disable sign ups
        #config.ACCOUNT_ALLOW_REGISTRATION = False
    
    elif dt >= config.ADMISSIONS_SELECTION_START and dt < config.ACADEMY_START:
            # Selection phase starts, applicants can not longer make submissions
            logger.info("Closing candidate applications...")
            logger.info("Opening candidate selection...")

            config.PORTAL_STATUS = "admissions:selection"
            # Disable sign ups
            config.ACCOUNT_ALLOW_REGISTRATION = False

    elif dt >= config.ACADEMY_START:
        config.PORTAL_STATUS = "academy"

