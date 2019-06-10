from django.urls import path, include

from . import views

app_name = "academy"

urlpatterns = [
    # Student Views
    path(r'student/units/',
         view=views.StudentUnitListView.as_view(),
         name='student-unit-list'),
    path(r'student/units/<str:pk>/',
         view=views.StudentUnitDetailView.as_view(),
         name='student-unit-detail'),

    # Instructor Views
    path(r'instructor/units/',
         view=views.InstructorUserListView.as_view(),
         name='instructor-user-list'),

    # API
    path(
        r'api/grades/<str:username>/units/<str:unit>/',
        views.GradingView.as_view(),
        name='grade',
    ),
    path(
        r'api/checksums/<str:pk>/',
        views.ChecksumView.as_view(),
        name='checksum',
    ),
]
