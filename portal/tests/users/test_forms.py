import pytest

from portal.users.forms import UserChangeForm, UserCreationForm
from portal.users.models import User


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


@pytest.mark.django_db()
def test_student_cannot_edit_reset_retention_in_profile():
    student = User.objects.create_user(
        username="profile-student",
        email="profile-student@example.com",
        is_student=True,
    )
    form = UserChangeForm(instance=student)
    assert "retain_student_account_on_next_edition_reset" not in form.fields
