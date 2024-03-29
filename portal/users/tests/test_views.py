import pytest  # noqa: D100
from django.conf import settings
from django.test import RequestFactory

from portal.users.views import UserRedirectView, UserUpdateView

pytestmark = pytest.mark.django_db


class TestUserUpdateView:

    """TODO.

    Extracting view initialization code as class-scoped fixture
    would be great if only pytest-django supported non-function-scoped
    fixture db access -- this is a work-in-progress for now:
    https://github.com/pytest-dev/pytest-django/pull/258
    """  # noqa: D211

    def test_get_success_url(  # noqa: ANN201, D102
        self,  # noqa: ANN101
        user: settings.AUTH_USER_MODEL,
        request_factory: RequestFactory,
    ):  # noqa: D102
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == "/users/profile/"  # noqa: S101

    def test_get_object(  # noqa: ANN201, D102
        self,  # noqa: ANN101
        user: settings.AUTH_USER_MODEL,
        request_factory: RequestFactory,
    ):  # noqa: D102
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user  # noqa: S101


class TestUserRedirectView:  # noqa: D101
    def test_get_redirect_url(  # noqa: ANN201, D102
        self,  # noqa: ANN101
        user: settings.AUTH_USER_MODEL,
        request_factory: RequestFactory,
    ):
        view = UserRedirectView()
        request = request_factory.get("/fake-url")
        request.user = user

        view.request = request

        assert view.get_redirect_url() == "/users/profile/"  # noqa: S101
