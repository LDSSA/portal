import pytest
from datetime import datetime

from .views import csvdata, InstructorUserListView


@pytest.mark.django_db(transaction=True)
def test_csvdata(db, specialization, slu1, slu2, student, grade_slu1, grade_slu2):
    specialization.unit_count = 2
    spc_list = [specialization]
    unit_list = [slu1, slu2]
    object_list = [
        {
            "user": student,
            "grades": [grade_slu1, grade_slu2],
            "submission_date": datetime(year=2021, month=8, day=15),
            "total_score": 38,
        }
    ]
    text = csvdata(spc_list, unit_list, object_list)
    assert text == "username,slack_id,submission_date,total_score,S01-SLU01,S01-SLU02\r\n" \
                   "test_student,U12J14XV12Z,2021-08-15 00:00:00,38,18,20\r\n"
