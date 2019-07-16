import string
import subprocess
import logging
import random
from urllib.parse import urljoin, unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


def get_ldsa_params():
    grader = get_user_model().objects.get(username=settings.GRADING_USERNAME)

    grading_url = reverse('academy:grade', args=('{username}', '{codename}'))
    grading_url = unquote(grading_url)
    grading_url = urljoin(settings.BASE_URL, grading_url)

    checksum_url = reverse('academy:checksum', args=('{codename}', ))
    checksum_url = unquote(checksum_url)
    checksum_url = urljoin(settings.BASE_URL, checksum_url)

    return {
        'token': grader.auth_token.key,
        'grading_url': grading_url,
        'checksum_url': checksum_url,
    }


def perform_grading_local(user, unit):
    params = get_ldsa_params()

    key = user.deploy_private_key.replace('\n', '|')
    process = subprocess.run(
        ["docker", "run", "--rm",
         "--network", "portal",
         "--env", f"LDSA_TOKEN={params['token']}",
         "--env", f"LDSA_GRADING_URL={params['grading_url']}",
         "--env", f"LDSA_CHECKSUM_URL={params['checksum_url']}",
         "--env", f"DEPLOY_KEY={key}",
         "--env", f"CODENAME={unit.code}",
         "--env", f"USERNAME={user.username}",
         f"{unit.code.lower()}"]
    )
    if process.returncode != 0:
        logger.critical('--------------------------------------------')
        logger.critical(process.returncode)
        logger.critical(process.stderr)
        logger.critical(process.stdout)
        logger.critical('--------------------------------------------')
        # raise RuntimeError("Error running grading")
        return

    else:
        logger.info("Graded %s %s", user.username, unit.code)


def perform_grading_production(user, unit):
    params = get_ldsa_params()
    key = user.deploy_private_key.replace('\n', '|')
    id_ = "".join(random.choices(string.ascii_lowercase, k=8))

    logger.info("Starting grading of `%s` for `%s`", unit.code, user.username)
    process = subprocess.Popen([
        "kubectl", "run", f"{unit.code.lower()}-{user.username.lower()}-{id_}",
        "--restart=Never",
        #"--requests='cpu=100m,memory=512Mi'",
        "--rm", "-i",  # "--tty",
        f"--image=ldssa/{unit.code.lower()}",
        "--env", f"LDSA_TOKEN={params['token']}",
        "--env", f"LDSA_GRADING_URL={params['grading_url']}",
        "--env", f"LDSA_CHECKSUM_URL={params['checksum_url']}",
        "--env", f"DEPLOY_KEY={key}",
        "--env", f"CODENAME={unit.code}",
        "--env", f"USERNAME={user.username}",
    ])

    logger.info("Graded %s %s", user.username, unit.code)
    logger.info(process.returncode)
