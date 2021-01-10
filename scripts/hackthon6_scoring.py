import json

from sklearn import metrics

from portal.capstone.models import DueDatapoint


def fairness_score_precision(sensitive_class):
    '''
    Computes a fairness score corresponding to the highest difference
     between precision among sensitive classes

    :param sensitive_class: dictionary with the following structure
      {
       'sensitive_class_1': {'outcomes': [...], 'predictions': [...]},
       'sensitive_class_2': {'outcomes': [...], 'predictions': [...]},
       ...
      }
    :return: maximum difference between precisions in sensitive clasess
    '''
    precisions = []
    for s_class in sensitive_class.keys():
        outcomes = sensitive_class[s_class]["outcomes"]
        predictions = sensitive_class[s_class]["predictions"]
        if len(outcomes) > 100:
            precisions.append(metrics.precision(outcomes, predictions))

    precision_diff = 0
    if precisions:
        precision_diff = max(precisions) - min(precisions)

    return precision_diff


def score(student_api):
    '''
    Calculates the score of the students' API model
    :param student_api: StudentApi object
    :return: score as a float
    '''

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
    sensitive_class_race = {}
    sensitive_class_sex = {}
    for ddp in qs:  # loop through each entry in DueDataPoint
        outcome = json.loads(ddp.datapoint.outcome)
        data = json.loads(ddp.datapoint.data)
        if ddp.response_status != 200:  # Missing or bad response
            predictions.append(not outcome)
            outcomes.append(outcome)

        else:
            try:
                prediction = json.loads(ddp.response_content)['prediction']
            except (json.JSONDecodeError, KeyError):
                predictions.append(not outcome)
                outcomes.append(outcome)
            else:
                sex = data["sex"].lower()
                if sex not in sensitive_class_sex:
                    sensitive_class_sex[sex] = {"outcomes": [], "predictions": []}

                sensitive_class_sex[sex]["outcomes"].append(outcome)
                sensitive_class_sex[sex]["predictions"].append(prediction)

                race = data["race"].lower()
                if race not in sensitive_class_race:
                    sensitive_class_race[race] = {"outcomes": [], "predictions": []}

                sensitive_class_race[race]["outcomes"].append(outcome)
                sensitive_class_race[race]["predictions"].append(prediction)
                if not isinstance(value, bool):
                    predictions.append(not outcome)
                else:
                    predictions.append(prediction)
                outcomes.append(outcome)

    f1_score = metrics.f1_score(outcomes, predictions, pos_label=True)

    race_diff = fairness_score_precision(sensitive_class_race)
    sex_diff = fairness_score_precision(sensitive_class_sex)

    is_fair = race_diff < 0.2 and sex_diff < 0.2
    if not is_fair:
        f1_score -= 0.1

    return f1_score
