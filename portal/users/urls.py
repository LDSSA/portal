from django.urls import path

from portal.users.views import (
    user_list_view,
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

app_name = "users"
urlpatterns = [
    # path("", view=user_list_view, name="list"),
    # path("~redirect/", view=user_redirect_view, name="redirect"),
    # TODO TODO TODO add profile fields from admissions
    path("profile/", view=user_update_view, name="profile"),
    # path("<str:username>/", view=user_detail_view, name="detail"),
]
