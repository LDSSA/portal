from django.urls import path, include

app_name = "admissions"

urlpatterns = [
    path("staff/", include("staff.urls")),
    path("candidate/", include("candidate.urls")),
]
