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
    help = "Score capstone"

    def add_arguments(self, parser):
        parser.add_argument("capstone")

    def handle(self, *args, **options):
        capstone = models.Capstone(name=options["capstone"])
        capstone.score()
