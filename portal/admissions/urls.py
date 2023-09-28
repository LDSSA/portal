from django.urls import include, path

app_name = "admissions"

urlpatterns = [
    path("staff/", include("portal.staff.urls")),
    path("candidate/", include("portal.candidate.urls")),
]
