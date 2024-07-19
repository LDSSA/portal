from django.urls import path  # noqa: D100

from . import views

app_name = "grading"

urlpatterns = [
    # Academy
    # https://portal.lisbondatascience.org/grading/academy/grade/{pk}/
    path(
        r"academy/grade/<str:pk>/",
        views.AcademyGradingView.as_view(),
        name="academy-grade",
    ),
    # https://portal.lisbondatascience.org/grading/academy/checksum/{pk}/
    path(
        r"academy/checksums/<str:pk>/",
        views.AcademyChecksumView.as_view(),
        name="academy-checksum",
    ),
    # Admissions
    # https://portal.lisbondatascience.org/grading/admissions/grades/{pk}/
    path(
        r"admissions/grade/<str:pk>/",
        views.AdmissionsGradingView.as_view(),
        name="admissions-grade",
    ),
    # https://portal.lisbondatascience.org/grading/admissions/checksums/{pk}/
    path(
        r"admissions/checksums/<str:pk>/",
        views.AdmissionsChecksumView.as_view(),
        name="admissions-checksum",
    ),
    path(
        r"admissions/notebook/<str:pk>/",
        views.AdmissionsNotebookDownload.as_view(),
        name="admissions-notebook",
    ),
]
