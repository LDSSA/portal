from django.urls import path, include

urlpatterns = [
    path("staff/", include("staff.urls")),
    path("candidate/", include("candidate.urls")),
]
