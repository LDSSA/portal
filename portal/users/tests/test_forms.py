import pytest  # noqa: D100

from portal.users.forms import UserCreationForm
from portal.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:  # noqa: D101
    def test_clean_username(self):  # noqa: D102
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = UserCreationForm(
            {
                "email": proto_user.email,
                "username": proto_user.username,
                "password1": proto_user.password,
                "password2": proto_user.password,
            }
        )

        assert form.is_valid()
        assert form.clean_username() == proto_user.username

        # Creating a user.
        form.save()

        # The user with proto_user params already exists,
        # hence cannot be created.
        form = UserCreationForm(
            {
                "email": proto_user.email,
                "username": proto_user.username,
                "password1": proto_user.password,
                "password2": proto_user.password,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
