import json

from sklearn import metrics

from portal.capstone.models import DueDatapoint

def score(student_api):
    '''
    Calculates the score of the students' API model

    :param student_api: StudentApi object
    :return: score as a float
    '''

    # Check which simulators have datapoints with outcomes outcomes
    simulator_ids = []
    for simulator in student_api.capstone.simulators.all():
        if simulator.datapoints.filter(outcome__isnull=False).count() > 0:
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
        if ddp.response_status != 200:  # Missing or bad response 
            predictions.append(1 - ddp.datapoint.outcome)  # TODO what to do??
            outcomes.append(ddp.datapoint.outcome)

        else:
            try:
                prediction = json.loads(ddp.response_content)['prediction']
            except (json.JSONDecodeError, KeyError):
                predictions.append(1 - ddp.datapoint.outcome)  # TODO what to do??
                outcomes.append(ddp.datapoint.outcome)

            else:
                predictions.append(prediction)
                outcomes.append(ddp.datapoint.outcome)

    # Score
    return metrics.roc_auc_score(outcomes, predictions)