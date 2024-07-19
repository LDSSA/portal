from django.urls import path  # noqa: D100

from portal.users.views import (
    user_update_view,
)

app_name = "users"
urlpatterns = [
    # path("", view=user_list_view, name="list"),  # noqa: ERA001
    # path("~redirect/", view=user_redirect_view, name="redirect"),  # noqa: ERA001
    path("profile/", view=user_update_view, name="profile"),
    # path("<str:username>/", view=user_detail_view, name="detail"),  # noqa: ERA001
]
