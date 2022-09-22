import logging
import random
import re
import string
import subprocess
from urllib.parse import urljoin, unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse


logger = logging.getLogger(__name__)
pattern = re.compile("[^a-zA-Z0-9-]+")


class MockGrading:
    def __init__(self, grade):
        pass

    def run_grading(self):
        pass

class Grading:
    def __init__(self, grade):
        self.grade = grade

    def get_command(self, image, name, env):
        raise NotImplementedError

    def get_env(self):
        raise NotImplementedError

    def get_image(self):
        raise NotImplementedError

    def get_name(self):
        raise NotImplementedError

    def start_message(self):
        logger.info(
            "Starting grading of `%s` for `%s`",
            self.grade.unit.pk,
            self.grade.user.username,
        )

    def success_message(self):
        logger.info(
            "Graded %s %s", self.grade.user.username, self.grade.unit.pk
        )

    def run_command(self, cmd):
        process = subprocess.run(cmd)
        if process.returncode != 0:
            logger.critical(
                "Error running container %s %s %s",
                process.returncode,
                process.stderr,
                process.stdout,
            )
            return

        else:
            self.success_message()

    def run_grading(self):
        image = self.get_image()
        name = self.get_name()
        env = self.get_env()
        cmd = self.get_command(image, name, env)
        self.start_message()
        logger.info(cmd)
        subprocess.Popen(cmd)


class KubernetesGrading(Grading):
    def get_command(self, image, name, env):
        """Run grading container in k8s"""
        CMD = [
            "kubectl",
            "run",
            name,
            "--restart=Never",
            # "--requests='cpu=100m,memory=512Mi'",
            "--rm",
            "-i",  # "--tty",
            f"--image={image}",
        ]
        for key, val in env.items():
            CMD.extend(["--env", f"{key}={val}"])
        return CMD


class DockerGrading(Grading):
    def get_command(self, image, name, env):
        CMD = [
            "/usr/bin/docker",
            "run",
            "--rm",
            "--network",
            "portal",
            "--name",
            name,
        ]
        for key, val in env.items():
            CMD.extend(["--env", f"{key}={val}"])
        CMD.append(image)
        return CMD


class AcademyGradingMixin:
    grading_view_name = "grading:academy-grade"
    checksum_view_name = "grading:academy-checksum"

    def get_grading_url(self):
        url = reverse(self.grading_view_name, args=(self.grade.pk,))
        url = unquote(url)
        return urljoin(settings.BASE_URL, url)

    def get_checksum_url(self):
        url = reverse(self.checksum_view_name, args=(self.grade.unit.pk,))
        url = unquote(url)
        return urljoin(settings.BASE_URL, url)

    def get_image(self):
        return f"ldssa/{settings.BASE_URL}-{self.grade.unit.code.lower()}"

    def get_name(self):
        id_ = "".join(random.choices(string.ascii_lowercase, k=8))
        username = self.grade.user.username.lower()[:50]
        name = f"{self.grade.unit.code.lower()}-{username}-{id_}"
        return pattern.sub("", name)

    def get_env(self):
        grader = get_user_model().objects.get(
            username=settings.GRADING_USERNAME
        )

        grading_url = self.get_grading_url()
        checksum_url = self.get_checksum_url()

        # Deploy key to clone user repo
        key = self.grade.user.deploy_private_key.replace("\n", "|")

        return {
            "LDSA_TOKEN": grader.auth_token.key,
            "PORTAL_TOKEN": grader.auth_token.key,
            "PORTAL_GRADING_URL": grading_url,
            "PORTAL_CHECKSUM_URL": checksum_url,
            "DEPLOY_KEY": key,
            "CODENAME": self.grade.unit.code,
            "USERNAME": self.grade.user.github_username,
            "REPO_NAME": settings.STUDENT_REPO_NAME,
        }


class AcademyKubernetesGrading(AcademyGradingMixin, KubernetesGrading):
    def run_command(self, cmd):
        """Do not wait for process to complete"""
        subprocess.Popen(cmd)


class AcademyDockerGrading(AcademyGradingMixin, KubernetesGrading):
    pass


class AdmissionsGradingMixin(AcademyGradingMixin):
    grading_view_name = "grading:admissions-grade"
    checksum_view_name = "grading:admissions-checksum"
    notebook_view_name = "grading:admissions-notebook"

    def get_image(self):
        return f"ldssa/{settings.BASE_URL}-admissions-{self.grade.unit.code.lower()}:latest"

    def get_env(self):
        env = super().get_env()
        notebook_url = reverse(self.notebook_view_name, args=(self.grade.pk,))
        notebook_url = unquote(notebook_url)
        notebook_url = urljoin(settings.BASE_URL, notebook_url)
        env["NOTEBOOK_URL"] = notebook_url
        return env


class AdmissionsKubernetesGrading(AdmissionsGradingMixin, KubernetesGrading):
    pass


class AdmissionsDockerGrading(AdmissionsGradingMixin, DockerGrading):
    pass
