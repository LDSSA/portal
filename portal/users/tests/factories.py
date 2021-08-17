from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from factory import Faker


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
