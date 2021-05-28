from django.urls import path

from . import views

app_name = "academy"

urlpatterns = [
    # Student Views
    path(
        r"student/units/",
        view=views.StudentUnitListView.as_view(),
        name="student-unit-list",
    ),
    path(
        r"student/units/<str:pk>/",
        view=views.StudentUnitDetailView.as_view(),
        name="student-unit-detail",
    ),
    # Instructor Views
    path(
        r"instructor/students/",
        view=views.InstructorUserListView.as_view(),
        name="instructor-user-list",
    ),
    path(
        r"instructor/units/",
        view=views.InstructorUnitListView.as_view(),
        name="instructor-unit-list",
    ),
    path(
        r"instructor/units/<str:pk>/",
        view=views.InstructorUnitDetailView.as_view(),
        name="instructor-unit-detail",
    ),
]
