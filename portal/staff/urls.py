from django.urls import path

from portal.staff import views

app_name = "staff"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("events", views.EventsView.as_view(), name="events"),
    path("candidates", views.CandidateListView.as_view(), name="candidate-list"),
    path(
        "candidates/<int:user_id>/",
        views.CandidateDetailView.as_view(),
        name="candidate-detail",
    ),
    path("applications", views.ApplicationView.as_view(), name="application-list"),
    path("submissions", views.SubmissionView.as_view(), name="submission-list"),
    path(
        "submissions/download/<int:submission_id>",
        views.SubmissionDownloadView.as_view(),
        name="submission-download",
    ),
    path(
        "submissions/download-feedback/<int:submission_id>",
        views.SubmissionFeedbackDownloadView.as_view(),
        name="submission-feedback-download",
    ),
    path("selections/", views.SelectionListView.as_view(), name="selection-list"),
    path(
        "selections/draw", views.SelectionDrawView.as_view(), name="selection-draw"
    ),
    path(
        "selections/reject-draw/<int:candidate_id>",
        views.SelectionRejectView.as_view(),
        name="selection-reject",
    ),
    path(
        "selections/select",
        views.SelectionSelectView.as_view(),
        name="selection-select",
    ),
    path("interviews", views.InterviewListView.as_view(), name="interview-list"),
    path(
        "interviews/<int:user_id>",
        views.InterviewDetailView.as_view(),
        name="interview-detail",
    ),
    path("payments", views.PaymentListView.as_view(), name="payment-list"),
    path(
        "payments/<int:user_id>",
        views.PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "payments/<int:user_id>/reset",
        views.PaymentResetView.as_view(),
        name="payment-reset",
    ),
    path("exports", views.ExportView, name="export"),
    path("export-candidates", views.ExportCandidatesView, name="export-candidates"),
]
