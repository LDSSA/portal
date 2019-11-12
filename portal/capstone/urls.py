from django.urls import path, include

from . import views

app_name = "capstone"

urlpatterns = [
    # Capstone Testing Views
    path(r'predict/',
         view=views.CapstonePredictView.as_view(),
         name='predict'),
    path(r'update/',
         view=views.CapstoneUpdateView.as_view(),
         name='update'),
]
