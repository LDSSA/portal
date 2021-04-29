from django.urls import path, include

from . import views

app_name = "capstone"

urlpatterns = [
    # Student Views
    path(
        r"student/capstones/",
        view=views.StudentCapstoneListView.as_view(),
        name="student-capstone-list",
    ),
    path(
        r"student/capstones/<str:pk>/",
        view=views.StudentCapstoneDetailView.as_view(),
        name="student-capstone-detail",
    ),
    # Instructor Views
    path(
        r"instructor/capstones/",
        view=views.InstructorCapstoneListView.as_view(),
        name="instructor-capstone-list",
    ),
    path(
        r"instructor/capstones/<str:pk>/",
        view=views.InstructorCapstoneDetailView.as_view(),
        name="instructor-capstone-detail",
    ),
    # Capstone Testing Views
    path(
        r"testing/<slug:app_name>/predict/",
        view=views.CapstonePredictView.as_view(),
        name="predict",
    ),
    path(
        r"testing/<slug:app_name>/update/",
        view=views.CapstoneUpdateView.as_view(),
        name="update",
    ),
]
