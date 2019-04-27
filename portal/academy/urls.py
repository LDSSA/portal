from django.urls import path, include

from . import views

app_name = "academy"



urlpatterns = [
    path(r'',
         view=views.UnitListView.as_view(),
         name='unit-list'),
    path(r'<str:pk>/',
         view=views.UnitDetailView.as_view(),
         name='unit-detail'),

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
