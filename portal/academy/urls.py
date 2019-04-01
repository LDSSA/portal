from django.urls import path

from . import views

app_name = "academy"
urlpatterns = [
    path("", view=views.UnitListView.as_view(), name="unit-list"),
    path("<str:pk>/", view=views.UnitDetailView.as_view(),
         name="unit-detail"),
]
