import logging
import random
from io import StringIO

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction

from . import models

logger = logging.getLogger(__name__)


def can_participate(user, hackathon):
    if not user.is_active or not user.is_student or user.failed_or_dropped:
        return False
    if not user.admissions_requires_exam:
        from portal.academy.services import progression_block_reason

        return not progression_block_reason(user)
    from portal.academy.models import Specialization
    from portal.academy.services import check_complete_specialization

    spec = Specialization.objects.filter(code="S" + hackathon.code[-2:]).first()
    return spec is not None and check_complete_specialization(user, spec)


@transaction.atomic
def generate_teams(hackathon, team_size=3, max_team_size=6, max_teams=13):
    if not (1 <= team_size <= max_team_size and max_teams >= 1):
        raise ValidationError("Invalid team size or team capacity.")
    models.Hackathon.objects.select_for_update().get(pk=hackathon.pk)
    present = list(
        models.Attendance.objects.filter(
            hackathon=hackathon,
            present=True,
            user__is_student=True,
            user__is_active=True,
            user__failed_or_dropped=False,
        ).select_related("user")
    )
    students = list({a.user_id: a.user for a in present}.values())
    students = [u for u in students if can_participate(u, hackathon)]
    for size in range(team_size, max_team_size + 1):
        groups = get_groups(students, size)
        if len(groups) <= max_teams:
            break
    else:
        raise ValidationError("Not enough team capacity for the present students.")
    if models.Submission.objects.filter(hackathon=hackathon).exists():
        raise ValidationError("Teams cannot be regenerated after submissions exist.")
    hackathon.teams.all().delete()
    create_teams(hackathon, groups)


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
    hackathon,
    team_size=3,
    max_team_size=6,
    max_teams=13,
):  # noqa:ANN201
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

    for _i in range(team_size, max_team_size + 1):
        present_teams = get_groups(present, team_size)
        remote_teams = get_groups(remote, team_size)

        if len(present_teams) + len(remote_teams) > max_teams:
            team_size += 1
            continue

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
        logger.info("(remote) Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1


def get_groups(items, size, max_diff=1):
    if size < 1:
        raise ValidationError("Team size must be positive.")
    items = list(items)
    if not items:
        return []
    random.shuffle(items)
    count = (len(items) + size - 1) // size
    return [items[i::count] for i in range(count)]


@transaction.atomic
def submission(hackathon, user, file):
    hackathon = models.Hackathon.objects.select_for_update().get(pk=hackathon.pk)
    if user.is_student:
        if hackathon.status not in ("submissions_open", "complete"):
            msg = "Hackathon closed"
            raise ValidationError(msg)

        # Replace students with team
        if hackathon.status == "submissions_open":
            team = models.Team.objects.filter(users=user, hackathon=hackathon).first()
            if team is None:
                raise ValidationError(
                    "You must belong to a team to submit during the hackathon."
                )
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
                    msg = "Max submissions"
                    raise ValidationError(msg)

    # Load hackathon functions
    glob = {}
    script = hackathon.script_file.read().decode()
    exec(script, glob)

    # Load true data
    y_true = StringIO(hackathon.data_file.read().decode())
    y_true = glob["load"](y_true)

    # Load prediction data
    try:
        y_pred = glob["load"](file)
    except Exception as exc:
        msg = "Error reading data"
        raise ValidationError(msg) from exc

    try:
        is_valid = glob["validate"](y_true, y_pred)
    except Exception as exc:
        msg = "Error validating data"
        raise ValidationError(msg) from exc

    if not is_valid:
        msg = "Invalid input"
        raise ValidationError(msg)

    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    score = glob["score"](y_true, y_pred)
    models.Submission.objects.create(
        hackathon=hackathon,
        content_type=ContentType.objects.get_for_model(user._meta.model),
        object_id=user.id,
        score=score,
    )

    return score
