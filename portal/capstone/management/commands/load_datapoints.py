from django.core.management.base import BaseCommand, CommandError


from portal.capstone import models


class Command(BaseCommand):
    help = 'Load file to datapoints'

    def add_arguments(self, parser):
        parser.add_argument('simulator_name')
        parser.add_argument('file')

    def handle(self, *args, **options):
        simulator = models.Simulator(name=options['simulator_name'])
        with open(options['file']) as fd:
            data = fd.read()

        datapoints = [
            models.Datapoint(simulator=simulator,
                             datapoint_id=entry['id'],
                             data=entry['data'])
            for entry in data]
        models.Datapoint.objects.bulk_create(datapoints)

        self.stdout.write(self.style.SUCCESS('Successfully created datapoints'))
