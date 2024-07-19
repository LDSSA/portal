from django.urls import include, path  # noqa: D100

app_name = "admissions"

urlpatterns = [
    path("staff/", include("portal.staff.urls")),
    path("candidate/", include("portal.candidate.urls")),
]
