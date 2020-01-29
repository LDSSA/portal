from datetime import datetime, timezone
from portal.capstone import models


student_api = models.StudentApi.objects.get(id=107)
simulator = models.Simulator.objects.get(name='extension_observations')
datapoints = simulator.datapoints.order_by('id').all()
starts = datetime.now(timezone.utc)
simulator.add_student_api(student_api, datapoints, )

