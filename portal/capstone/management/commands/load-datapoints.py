import json  # noqa: D100, N999
from pathlib import Path

from django.core.management.base import BaseCommand

from portal.capstone import models


class Command(BaseCommand):  # noqa: D101
    help = "Load file to datapoints"  # noqa: A003

    def add_arguments(self, parser):  # noqa: ANN001, ANN101, ANN201, D102
        parser.add_argument("simulator_name")
        parser.add_argument("--data", required=True)
        parser.add_argument("--batch-size", type=int, default=1000)

    def handle(self, *args, **options):  # noqa: ANN002, ANN003, ANN101, ANN201, ARG002, D102
        simulator = models.Simulator.objects.get(name=options["simulator_name"])

        with Path(options["data"]).open() as handle:
            data = json.loads(handle.read())

        self.stdout.write(self.style.SUCCESS("Creating datapoint objects batch 1"))
        datapoints = []
        idx = 0
        for idx, datapoint in enumerate(data):
            dp = models.Datapoint(
                simulator=simulator,
                data=json.dumps(datapoint["data"]),
                outcome=json.dumps(datapoint.get("outcome", "")),
            )
            datapoints.append(dp)

            if (idx + 1) % options["batch_size"] == 0:
                batch_num = (idx // options["batch_size"]) + 1
                self.stdout.write(self.style.SUCCESS(f"Storing in database batch {batch_num}"))
                models.Datapoint.objects.bulk_create(datapoints)

                self.stdout.write(
                    self.style.SUCCESS(f"Creating datapoint objects batch {batch_num + 1}"),
                )
                datapoints = []

        if datapoints:
            batch_num = idx // options["batch_size"]
            self.stdout.write(self.style.SUCCESS(f"Storing in database batch {batch_num}"))
            models.Datapoint.objects.bulk_create(datapoints)

        self.stdout.write(self.style.SUCCESS("Successfully created datapoints"))
