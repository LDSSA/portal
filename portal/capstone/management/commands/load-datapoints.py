import json

import pandas as pd
from django.core.management.base import BaseCommand

from portal.capstone import models


class Command(BaseCommand):
    help = 'Load file to datapoints'

    def add_arguments(self, parser):
        parser.add_argument('simulator_name')
        parser.add_argument('file')

    def handle(self, *args, **options):
        simulator = models.Simulator.objects.get(
            name=options['simulator_name'])
        df = pd.read_csv(options['file'])
        datapoints = [
            models.Datapoint(simulator=simulator,
                             data=json.dumps(data.to_dict()))
            for _, data in df.iterrows()]
        models.Datapoint.objects.bulk_create(datapoints)

        self.stdout.write(
            self.style.SUCCESS('Successfully created datapoints'))
