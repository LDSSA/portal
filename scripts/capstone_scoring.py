import json

from sklearn import metrics
from portal.capstone.models import DueDatapoint


def score(student_api):
    """
    Calculates the score of the students' API model
    :param student_api: StudentApi object
    :return: score as a float
    """

    # Check which simulators have datapoints with outcomes outcomes
    simulator_ids = []
    for simulator in student_api.capstone.simulators.all():
        if simulator.datapoints.exclude(outcome="").count() > 0:
            simulator_ids.append(simulator.id)

    if len(simulator_ids) == 0:
        raise RuntimeError("No simulators with outcomes found.")

    qs = DueDatapoint.objects.filter(
        simulator_id__in=simulator_ids,
        student=student_api.student,
    )
    outcomes = []
    predictions = []
    for ddp in qs:  # loop through each entry in DueDataPoint
        outcome = bool(json.loads(ddp.datapoint.outcome))
        data = json.loads(ddp.datapoint.data)
        if ddp.response_status != 200:  # Missing or bad response
            predictions.append(not outcome)
            outcomes.append(outcome)

        else:
            try:
                prediction = json.loads(ddp.response_content)["prediction"]
            except (json.JSONDecodeError, KeyError):
                predictions.append(not outcome)
                outcomes.append(outcome)
            else:
                if not isinstance(prediction, bool):
                    predictions.append(not outcome)
                else:
                    predictions.append(prediction)
                outcomes.append(outcome)

    recall = metrics.recall_score(outcomes, predictions, pos_label=True)
    return recall
