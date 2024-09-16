from django.urls import path

from portal.users.views import (
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("profile/", view=user_update_view, name="profile"),
]
