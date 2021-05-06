import json
from portal.capstone import models

file = "/tmp/moment_4_new.json"
moment = "Moment 4"
with open(file) as h:
    data = json.loads(h.read())

sim = models.Simulator.objects.get(name=moment)

for dp, row in zip(
    models.Datapoint.objects.filter(simulator=sim).order_by("id").all()[:200],
    data[:200],
):
    print(json.loads(dp.data)["observation_id"], row["data"]["observation_id"])

for dp, row in zip(
    models.Datapoint.objects.filter(simulator=sim).order_by("id").iterator(),
    data,
):
    dp.outcome = json.dumps(row["outcome"])
    dp.save()
