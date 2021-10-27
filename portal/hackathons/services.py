import logging
import random
from itertools import zip_longest
from io import StringIO

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from . import models


logger = logging.getLogger(__name__)


def generate_teams(hackathon, team_size=3, max_team_size=6, max_teams=13):
    logger.info(
        "Generating Teams Size: %s Max: %s Max teams: %s",
        team_size,
        max_team_size,
        max_teams,
    )
    present = models.Attendance.objects.filter(
        hackathon=hackathon, present=True
    )
    present = [p.user for p in present]
    logger.debug("Present %s", present)

    for i in range(team_size, max_team_size + 1):
        present_teams = get_groups(present, team_size)

        if len(present_teams) > max_teams:
            team_size += 1
            continue
        else:
            break
    else:
        raise RuntimeError("Cannot fit with these parameters")

    create_teams(hackathon, present_teams)


def create_teams(hackathon, present_teams):
    hackathon_team_id = 1
    for students in present_teams:
        team = models.Team.objects.create(
            hackathon=hackathon, hackathon_team_id=hackathon_team_id
        )
        team.users.set(students)
        logger.info("Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1


def generate_teams_with_remote(
    hackathon, team_size=3, max_team_size=6, max_teams=13
):
    logger.info(
        "Generating Teams Size: %s Max: %s Max teams: %s",
        team_size,
        max_team_size,
        max_teams,
    )
    present = models.Attendance.objects.filter(
        hackathon=hackathon, present=True, remote=False
    )
    present = [p.user for p in present]
    remote = models.Attendance.objects.filter(
        hackathon=hackathon, present=True, remote=True
    )
    remote = [p.user for p in remote]
    logger.debug("Present %s", present)
    logger.debug("Remote %s", remote)

    for i in range(team_size, max_team_size + 1):
        present_teams = get_groups(present, team_size)
        remote_teams = get_groups(remote, team_size)

        if len(present_teams) + len(remote_teams) > max_teams:
            team_size += 1
            continue
        else:
            break
    else:
        raise RuntimeError("Cannot fit with these parameters")

    create_teams(hackathon, present_teams, remote_teams)


def create_teams_with_remote(hackathon, present_teams, remote_teams):
    hackathon_team_id = 1
    for students in present_teams:
        team = models.Team.objects.create(
            hackathon=hackathon, hackathon_team_id=hackathon_team_id
        )
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
        logger.info(
            "(remote) Team %s students %s", hackathon_team_id, students
        )
        hackathon_team_id += 1


def get_groups(items, size, max_diff=1):
    if not len(items):
        return []

    logger.debug("Creating groups...")
    random.shuffle(items)
    iterators = [iter(items)] * size
    groups = list(
        [item for item in group if item is not None]
        for group in zip_longest(*iterators)
    )
    logger.debug(groups)

    logger.debug("Reshaping groups...")
    idx = 0
    while (size - len(groups[-1])) > max_diff:
        item = groups[-2 - idx].pop()
        groups[-1].append(item)
        idx += 1
    logger.debug(groups)

    return groups


def submission(hackathon, user, file):
    if user.is_student:
        if hackathon.status not in ("submissions_open", "complete"):
            raise ValidationError("Hackathon closed")

        # Replace students with team
        if hackathon.status == "submissions_open":
            team = models.Team.objects.filter(
                users=user, hackathon=hackathon
            ).first()
            if team:
                user = team

                # Check submission limit
                num = models.Submission.objects.filter(
                    hackathon=hackathon,
                    content_type__app_label=user._meta.app_label,
                    content_type__model=user._meta.model_name,
                    object_id=user.id,
                ).count()
                if num >= hackathon.max_submissions:
                    raise ValidationError("Max submissions")

    # Load hackathon functions
    glob = {}
    script = hackathon.script_file.read().decode()
    exec(script, glob)

    # Load true data
    y_true = StringIO(hackathon.data_file.read().decode())
    y_true = glob["load"](y_true)

    # Load prediction data
    y_pred = glob["load"](file)

    try:
        is_valid = glob["validate"](y_true, y_pred)
    except Exception as exc:
        raise ValidationError("Error validating data") from exc

    if not is_valid:
        raise ValidationError("Invalid input")

    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    score = glob["score"](y_true, y_pred)
    models.Submission.objects.create(
        hackathon=hackathon,
        content_type=ContentType.objects.get_for_model(user._meta.model),
        object_id=user.id,
        score=score,
    )

    return score
