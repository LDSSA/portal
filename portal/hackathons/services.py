import logging  # noqa: D100
import random
from io import StringIO
from itertools import zip_longest

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from . import models

logger = logging.getLogger(__name__)


def generate_teams(  # noqa: ANN201, D103
    hackathon, team_size=3, max_team_size=6, max_teams=13  # noqa: ANN001
):  # noqa: ANN001, ANN201, D103
    logger.info(
        "Generating Teams Size: %s Max: %s Max teams: %s",
        team_size,
        max_team_size,
        max_teams,
    )
    present = models.Attendance.objects.filter(hackathon=hackathon, present=True)
    present = [p.user for p in present]
    logger.debug("Present %s", present)

    for _i in range(team_size, max_team_size + 1):
        present_teams = get_groups(present, team_size)

        if len(present_teams) > max_teams:
            team_size += 1
            continue

    create_teams(hackathon, present_teams)


def create_teams(hackathon, present_teams):  # noqa: ANN001, ANN201, D103
    hackathon_team_id = 1
    for students in present_teams:
        team = models.Team.objects.create(hackathon=hackathon, hackathon_team_id=hackathon_team_id)
        team.users.set(students)
        logger.info("Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1


def generate_teams_with_remote(  # noqa: ANN201, D103
    hackathon, team_size=3, max_team_size=6, max_teams=13  # noqa: ANN001
):  # noqa:ANN201
    logger.info(
        "Generating Teams Size: %s Max: %s Max teams: %s",
        team_size,
        max_team_size,
        max_teams,
    )
    present = models.Attendance.objects.filter(hackathon=hackathon, present=True, remote=False)
    present = [p.user for p in present]
    remote = models.Attendance.objects.filter(hackathon=hackathon, present=True, remote=True)
    remote = [p.user for p in remote]
    logger.debug("Present %s", present)
    logger.debug("Remote %s", remote)

    for _i in range(team_size, max_team_size + 1):
        present_teams = get_groups(present, team_size)
        remote_teams = get_groups(remote, team_size)

        if len(present_teams) + len(remote_teams) > max_teams:
            team_size += 1
            continue

    create_teams(hackathon, present_teams, remote_teams)


def create_teams_with_remote(hackathon, present_teams, remote_teams):  # noqa: ANN001, ANN201, D103
    hackathon_team_id = 1
    for students in present_teams:
        team = models.Team.objects.create(hackathon=hackathon, hackathon_team_id=hackathon_team_id)
        team.users.set(students)
        logger.info("Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1

    for students in remote_teams:
        team = models.Team.objects.create(
            hackathon=hackathon,
            hackathon_team_id=hackathon_team_id,
            remote=True,
        )
        team.users.set(students)
        logger.info("(remote) Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1


def get_groups(items, size, max_diff=1):  # noqa: ANN001, ANN201, D103
    if not len(items):
        return []

    logger.debug("Creating groups...")
    random.shuffle(items)
    iterators = [iter(items)] * size
    groups = [[item for item in group if item is not None] for group in zip_longest(*iterators)]
    logger.debug(groups)

    logger.debug("Reshaping groups...")
    idx = 0
    while (size - len(groups[-1])) > max_diff:
        item = groups[-2 - idx].pop()
        groups[-1].append(item)
        idx += 1
    logger.debug(groups)

    return groups


def submission(hackathon, user, file):  # noqa: ANN001, ANN201, D103
    if user.is_student:
        if hackathon.status not in ("submissions_open", "complete"):
            msg = "Hackathon closed"
            raise ValidationError(msg)

        # Replace students with team
        if hackathon.status == "submissions_open":
            team = models.Team.objects.filter(users=user, hackathon=hackathon).first()
            if team:
                user = team

                # Check submission limit
                num = models.Submission.objects.filter(
                    hackathon=hackathon,
                    content_type__app_label=user._meta.app_label,  # noqa: SLF001
                    content_type__model=user._meta.model_name,  # noqa: SLF001
                    object_id=user.id,
                ).count()
                if num >= hackathon.max_submissions:
                    msg = "Max submissions"
                    raise ValidationError(msg)

    # Load hackathon functions
    glob = {}
    script = hackathon.script_file.read().decode()
    exec(script, glob)  # noqa: S102

    # Load true data
    y_true = StringIO(hackathon.data_file.read().decode())
    y_true = glob["load"](y_true)

    # Load prediction data
    try:
        y_pred = glob["load"](file)
    except Exception as exc:  # noqa: BLE001
        msg = "Error reading data"
        raise ValidationError(msg) from exc

    try:
        is_valid = glob["validate"](y_true, y_pred)
    except Exception as exc:  # noqa: BLE001
        msg = "Error validating data"
        raise ValidationError(msg) from exc

    if not is_valid:
        msg = "Invalid input"
        raise ValidationError(msg)

    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    score = glob["score"](y_true, y_pred)
    models.Submission.objects.create(
        hackathon=hackathon,
        content_type=ContentType.objects.get_for_model(user._meta.model),  # noqa: SLF001
        object_id=user.id,
        score=score,
    )

    return score
