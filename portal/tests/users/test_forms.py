import pytest

from portal.users.forms import UserCreationForm


@pytest.mark.django_db()
def test_clean_username():
    form = UserCreationForm(
        {
            "email": "user@email.com",
            "username": "user",
            "password1": "82xx12300",
            "password2": "82xx12300",
        },
    )
    assert not form.errors
    assert form.clean_username() == "user"

    # Creating a user.
    form.save()

    # User with the same params already exists,
    # hence cannot be created.
    form = UserCreationForm(
        {
            "email": "user@email.com",
            "username": "user",
            "password1": "82xx12300",
            "password2": "82xx12300",
        },
    )

    assert form.errors
    assert "username" in form.errors
