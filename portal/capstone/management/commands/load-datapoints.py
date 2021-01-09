import json

from django.core.management.base import BaseCommand

from portal.capstone import models


class Command(BaseCommand):
    help = 'Load file to datapoints'

    def add_arguments(self, parser):
        parser.add_argument('simulator_name')
        parser.add_argument('--data', required=True)
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **options):
        simulator = models.Simulator.objects.get(
            name=options['simulator_name'])

        with open(options['data']) as handle:
            data = json.loads(handle.read())

        self.stdout.write(
            self.style.SUCCESS('Creating datapoint objects batch 1'))
        datapoints = []
        idx = 0
        for idx, datapoint in enumerate(data):
            dp = models.Datapoint(
                simulator=simulator, 
                data=json.dumps(data['data']), 
                outcome=json.dumps(data.get('outcome', '')),
                )
            datapoints.append(dp)

            if (idx + 1) % options['batch_size'] == 0:
                batch_num = (idx // options['batch_size']) + 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Storing in database batch {batch_num}'))
                models.Datapoint.objects.bulk_create(datapoints)

                self.stdout.write(
                    self.style.SUCCESS("Creating datapoint objects batch "
                                       f"{batch_num + 1}"))
                datapoints = []

        if datapoints:
            batch_num = (idx // options['batch_size'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'Storing in database batch {batch_num}'))
            models.Datapoint.objects.bulk_create(datapoints)

        self.stdout.write(
            self.style.SUCCESS('Successfully created datapoints'))
