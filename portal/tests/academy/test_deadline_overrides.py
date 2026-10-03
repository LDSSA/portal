import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from portal.academy.models import Grade, GradeDeadlineDecision
from portal.academy.services import (
    check_complete_specialization,
    check_graduation_status,
    get_best_grade,
    progression_block_reason,
    set_deadline_override,
)
from portal.grading.serializers import GradeSerializer
from portal.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def superuser():
    return User.objects.create(
        username="deadline-admin", is_staff=True, is_superuser=True
    )


@pytest.fixture
def late_grade(student, slu1):
    student.admissions_mode = "no_exam"
    student.save()
    return Grade.objects.create(
        user=student, unit=slu1, status="graded", score=20, on_time=False
    )


def test_override_requires_superuser_and_reason(late_grade, instructor, superuser):
    with pytest.raises(PermissionDenied):
        set_deadline_override(late_grade.pk, instructor, True, "Portal outage")
    with pytest.raises(ValidationError):
        set_deadline_override(late_grade.pk, superuser, True, "  ")
    late_grade.refresh_from_db()
    assert late_grade.deadline_valid_override is None
    assert not GradeDeadlineDecision.objects.exists()


def test_valid_exception_preserves_evidence_and_restores_progress(
    late_grade, superuser
):
    timestamp = late_grade.created
    user = late_grade.user
    assert progression_block_reason(user)
    updated = set_deadline_override(
        late_grade.pk, superuser, True, "Portal was offline before the deadline"
    )
    assert updated.created == timestamp
    assert updated.on_time is False
    assert updated.deadline_valid
    assert get_best_grade(updated.unit, user).pk == updated.pk
    assert check_complete_specialization(user, updated.unit.specialization)
    assert check_graduation_status(user)
    assert not progression_block_reason(user)
    event = updated.deadline_decisions.get()
    assert event.actor == superuser
    assert event.previous_value is None
    assert event.new_value is True
    assert event.reason == "Portal was offline before the deadline"
    set_deadline_override(
        updated.pk, superuser, None, "Exception reversed after investigation"
    )
    updated.refresh_from_db()
    assert not updated.deadline_valid
    assert updated.created == timestamp
    assert updated.deadline_decisions.count() == 2
    assert progression_block_reason(user)


def test_deadline_override_does_not_fabricate_a_passing_grade(late_grade, superuser):
    late_grade.status = "failed"
    late_grade.save()
    updated = set_deadline_override(
        late_grade.pk, superuser, True, "Deadline exception only"
    )
    assert not check_complete_specialization(updated.user, updated.unit.specialization)


def test_stale_grader_callback_cannot_erase_override(late_grade, superuser):
    set_deadline_override(late_grade.pk, superuser, True, "Portal incident")
    serializer = GradeSerializer(
        late_grade,
        data={"score": 18, "on_time": True, "deadline_valid_override": False},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    late_grade.refresh_from_db()
    assert late_grade.deadline_valid_override is True
    assert late_grade.on_time is False
    assert late_grade.score == 18


def test_admin_requires_justification_and_cannot_rewrite_original_lateness(
    client, late_grade, superuser
):
    client.force_login(superuser)
    url = reverse("admin:academy_grade_change", args=[late_grade.pk])
    data = {
        "unit": late_grade.unit_id,
        "user": late_grade.user_id,
        "status": "graded",
        "score": "20",
        "deadline_valid_override": "true",
        "deadline_override_reason": "",
        "message": "",
        "on_time": "on",
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert b"Explain why" in response.content
    assert not GradeDeadlineDecision.objects.exists()
    data["deadline_override_reason"] = "Portal outage"
    response = client.post(url, data)
    assert response.status_code == 302
    late_grade.refresh_from_db()
    assert late_grade.on_time is False
    assert late_grade.deadline_valid_override is True
    assert late_grade.deadline_decisions.get().actor == superuser


def test_ordinary_staff_cannot_override_via_admin(client, late_grade, instructor):
    from django.contrib.auth.models import Permission

    instructor.is_staff = True
    instructor.save()
    instructor.user_permissions.add(Permission.objects.get(codename="change_grade"))
    client.force_login(instructor)
    response = client.post(
        reverse("admin:academy_grade_change", args=[late_grade.pk]),
        {
            "unit": late_grade.unit_id,
            "user": late_grade.user_id,
            "status": "graded",
            "score": "20",
            "deadline_valid_override": "true",
            "deadline_override_reason": "Unauthorized",
            "on_time": "on",
            "message": "",
        },
    )
    assert response.status_code == 302
    late_grade.refresh_from_db()
    assert late_grade.deadline_valid_override is None
    assert not late_grade.on_time
    assert not GradeDeadlineDecision.objects.exists()
