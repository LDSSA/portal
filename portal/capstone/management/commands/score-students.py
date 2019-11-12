import sys
import json
import argparse
import pandas as pd
from sklearn.metrics import roc_auc_score
from playhouse.shortcuts import model_to_dict

# import settings
import models

import json

import pandas as pd
from django.core.management.base import BaseCommand

from portal.capstone import models
from portal.users.models import User


class Command(BaseCommand):
    help = 'Load file to datapoints'

    def add_arguments(self, parser):
        parser.add_argument('simulator_name')
        parser.add_argument('file')

    def handle(self, *args, **options):
        simulator = models.Simulator(name=options['simulator_name'])
        self.stdout.write('username, score')
        for student in User.objects.filter(student=True):
            score = self.score_student(simulator, student)
            self.stdout.write(
                f'{student.username}, {score}')

    def score_student(self, simulator, student):
        pass
