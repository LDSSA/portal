import pytest  # noqa: D100

pytestmark = pytest.mark.django_db


# def test_user_get_absolute_url(user: settings.AUTH_USER_MODEL):
#     assert user.get_absolute_url() == f"/users/{user.username}/"
