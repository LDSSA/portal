from django.urls import path, include
from rest_framework import routers

from . import views

app_name = "academy"

router = routers.DefaultRouter()
router.register(r'grades', views.GradingViewSet)
router.register(r'checksums', views.ChecksumViewSet)


urlpatterns = [
    # API
    path(r'', include(router.urls)),


    path(r'',
         view=views.UnitListView.as_view(),
         name='unit-list'),
    path(r'<str:pk>/',
         view=views.UnitDetailView.as_view(),
         name='unit-detail'),
]
