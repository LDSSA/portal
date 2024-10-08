from datetime import datetime

import pytest
from dateutil import tz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from factory import Faker
from factory.django import DjangoModelFactory

from portal.academy.models import Grade, Specialization, Unit
from portal.hackathons.models import Attendance, Hackathon
from portal.users.models import User

LISBON_TZ = tz.gettz("Europe/Lisbon")


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    password = Faker(
        "password",
        length=42,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


@pytest.fixture
def proto_user():
    return UserFactory()


@pytest.mark.django_db()
@pytest.fixture(autouse=True)
def _cleanup_db() -> None:
    User.objects.all().delete()
    Specialization.objects.all().delete()
    Unit.objects.all().delete()
    Grade.objects.all().delete()
    Attendance.objects.all().delete()
    Hackathon.objects.all().delete()


@pytest.fixture()
def grader():
    return User.objects.create(
        email=Faker("email"),
        username="grader",
        name="Grader User",
        github_username="GraderUser",
        slack_member_id="GRADER1234",
        is_student=True,
        is_instructor=True,
        is_staff=True,
    )


@pytest.fixture()
def student():
    return User.objects.create(
        email=Faker("email"),
        username="test_student",
        name="test_student",
        github_username="TestUser",
        slack_member_id="U12J14XV12Z",
        is_student=True,
        is_instructor=False,
    )


@pytest.fixture()
def student2():
    return User.objects.create(
        email=Faker("email"),
        username="test_student_2",
        name="test_student_2",
        github_username="TestUser2",
        slack_member_id="U12J144442Z",
        is_student=True,
        is_instructor=False,
    )


@pytest.fixture()
def instructor():
    return User.objects.create(
        email=Faker("email"),
        username="test_instructor",
        name="test_instructor",
        github_username="TestInstructor",
        slack_member_id="U8474XV12Z",
        is_student=False,
        is_instructor=True,
    )


@pytest.fixture()
def specialization():
    return Specialization.objects.create(
        code="S01",
        name="bootcamp",
        description="This is a test bootcamp",
        created=datetime(year=2021, month=8, day=10, tzinfo=LISBON_TZ),
    )


@pytest.fixture()
def slu1(specialization, instructor):
    return Unit.objects.create(
        specialization=specialization,
        code="SLU01",
        name="unit 1",
        description="This is a test unit",
        instructor=instructor,
        due_date=datetime(year=2021, month=8, day=30, tzinfo=LISBON_TZ),
        open=True,
        checksum="a424e2aa-adb2-473c-b782-65b9f879a628",
        created=datetime(year=2021, month=8, day=11, tzinfo=LISBON_TZ),
    )


@pytest.fixture()
def slu2(specialization, instructor):
    return Unit.objects.create(
        specialization=specialization,
        code="SLU02",
        name="unit 2",
        description="This is a test unit",
        instructor=instructor,
        due_date=datetime(year=2021, month=8, day=30, tzinfo=LISBON_TZ),
        open=True,
        checksum="a424e2aa-adb2-473c-b782-65b9f879a628",
        created=datetime(year=2021, month=8, day=11, tzinfo=LISBON_TZ),
    )


@pytest.fixture()
def hackathon1(specialization, instructor):
    return Hackathon.objects.create(
        code="HCKT01",
        name="Hackathon 1 - Binary classification",
        due_date=datetime(year=2021, month=8, day=30, tzinfo=LISBON_TZ),
        descending=False,
    )


@pytest.fixture()
def hackathon2(specialization, instructor):
    return Hackathon.objects.create(
        code="HCKT02",
        name="Hackathon 2 - Data wrangling",
        due_date=datetime(year=2021, month=9, day=30, tzinfo=LISBON_TZ),
        descending=False,
    )


@pytest.fixture()
def hackathon3(specialization, instructor):
    return Hackathon.objects.create(
        code="HCKT03",
        name="Hackathon 3 - Time series",
        due_date=datetime(year=2021, month=10, day=30, tzinfo=LISBON_TZ),
        descending=True,
    )


@pytest.fixture()
def grade_slu1(student, slu1):
    return Grade.objects.create(
        user=student,
        unit=slu1,
        created=datetime(year=2021, month=8, day=15, tzinfo=LISBON_TZ),
        status="graded",
        score=18,
        message="",
    )


@pytest.fixture()
def grade_slu2(student, slu2):
    return Grade.objects.create(
        user=student,
        unit=slu2,
        created=datetime(year=2021, month=8, day=15, tzinfo=LISBON_TZ),
        status="graded",
        score=20,
        message="",
    )


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture()
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()


@pytest.fixture()
def request_factory() -> RequestFactory:
    return RequestFactory()
