from django.urls import path, include

app_name = "admissions"

urlpatterns = [
    path("staff/", include("portal.staff.urls")),
    path("candidate/", include("portal.candidate.urls")),
]
