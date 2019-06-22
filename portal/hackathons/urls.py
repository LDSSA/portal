from django.urls import path

from . import views

app_name = "hackathons"

urlpatterns = [
    # Leaderboard
    path(r'student/hackathons/<str:pk>/leaderboard/',
         view=views.LeaderboardView.as_view(),
         name='leaderboard'),

    # API
    path(
        r'api/<str:code>/submit/',
        views.submission,
        name='student-submit',
    ),

    # Student Views
    path(r'student/hackathons/',
         view=views.StudentHackathonListView.as_view(),
         name='student-hackathon-list'),
    path(r'student/hackathons/<str:pk>/',
         view=views.StudentHackathonDetailView.as_view(),
         name='student-hackathon-detail'),

    # Instructor Views
    path(r'instructor/hackathons/',
         view=views.InstructorHackathonListView.as_view(),
         name='instructor-hackathon-list'),
    path(r'instructor/hackathons/<str:pk>/settings',
         view=views.InstructorHackathonSettingsView.as_view(),
         name='instructor-hackathon-settings'),
    path(r'instructor/hackathons/<str:pk>/',
         view=views.InstructorHackathonDetailView.as_view(),
         name='instructor-hackathon-detail'),

]
