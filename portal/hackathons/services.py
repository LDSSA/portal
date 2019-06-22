import logging
import random
from itertools import zip_longest

from . import models


logger = logging.getLogger(__name__)


def create_teams(hackathon, present_teams, remote_teams):
    hackathon_team_id = 1
    for students in present_teams:
        team = models.Team.objects.create(
            hackathon=hackathon,
            hackathon_team_id=hackathon_team_id)
        team.students.set(students)
        logger.info("Team %s students %s", hackathon_team_id, students)
        hackathon_team_id += 1

    for students in remote_teams:
        team = models.Team.objects.create(
            hackathon=hackathon,
            hackathon_team_id=hackathon_team_id,
            remote=True)
        team.students.set(students)
        logger.info("(remote) Team %s students %s",
                    hackathon_team_id, students)
        hackathon_team_id += 1


def generate_teams(hackathon, team_size=3, max_team_size=6, max_teams=13):
    present = models.Attendance.objects.filter(present=True, remote=False)
    present = [p.student for p in present]
    remote = models.Attendance.objects.filter(present=True, remote=True)
    remote = [p.student for p in remote]

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


def get_groups(items, size, max_diff=1):
    if not len(items):
        return []

    logger.debug('Creating groups...')
    random.shuffle(items)
    iterators = [iter(items)] * size
    groups = list([item for item in group if item is not None]
                  for group in zip_longest(*iterators))
    logger.debug(groups)

    logger.debug('Reshaping groups...')
    idx = 0
    while (size - len(groups[-1])) > max_diff:
        item = groups[-2 - idx].pop()
        groups[-1].append(item)
        idx += 1
    logger.debug(groups)

    return groups
