import subprocess
import logging
from urllib.parse import urljoin, unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


def perform_grading_local(user, unit):
    # Start grader
    grader = get_user_model().objects.get(username=settings.GRADING_USERNAME)

    grading_url = reverse('academy:grade', args=('{username}', '{codename}'))
    grading_url = unquote(grading_url)
    grading_url = urljoin(settings.BASE_URL, grading_url)

    checksum_url = reverse('academy:checksum', args=('{codename}', ))
    checksum_url = unquote(checksum_url)
    checksum_url = urljoin(settings.BASE_URL, checksum_url)

    key = user.deploy_private_key.replace('\n', '|')
    process = subprocess.run(
        ["docker", "run", "--rm",
         "--network", "portal",
         "--env", f"LDSA_TOKEN={grader.auth_token.key}",
         "--env", f"LDSA_GRADING_URL={grading_url}",
         "--env", f"LDSA_CHECKSUM_URL={checksum_url}",
         "--env", f"DEPLOY_KEY={key}",
         "--env", f"CODENAME={unit.code}",
         "--env", f"USERNAME={user.username}",
         f"{unit.code.lower()}"]
    )
    if process.returncode != 0:
        logger.critical('--------------------------------------------')
        logger.critical(process.stderr)
        logger.critical('--------------------------------------------')
        # raise RuntimeError("Error running grading")
        return

    else:
        logger.info("Graded %s %s", user.username, unit.code)


def perform_grading_production(user, unit):
    pass
