import pytest  # noqa: D100

pytestmark = pytest.mark.django_db


# def test_detail(user: settings.AUTH_USER_MODEL):
#     assert (
#         reverse("users:detail", kwargs={"username": user.username})  # noqa: ERA001
#         == f"/users/{user.username}/"
#     )  # noqa: ERA001
#     assert resolve(f"/users/{user.username}/").view_name == "users:detail"  # noqa: ERA001
#
#
# def test_list():
#     assert reverse("users:list") == "/users/"  # noqa: ERA001
#     assert resolve("/users/").view_name == "users:list"  # noqa: ERA001
#
#
# def test_update():
#     assert reverse("users:update") == "/users/~update/"  # noqa: ERA001
#     assert resolve("/users/~update/").view_name == "users:update"  # noqa: ERA001
#
#
# def test_redirect():
#     assert reverse("users:redirect") == "/users/~redirect/"  # noqa: ERA001
#     assert resolve("/users/~redirect/").view_name == "users:redirect"  # noqa: ERA001
