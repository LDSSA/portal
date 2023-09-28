from django.contrib.auth import get_user_model  # noqa: D100
from factory import Faker
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):  # noqa: D101
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

    class Meta:  # noqa: D106
        model = get_user_model()
        django_get_or_create = ["username"]
