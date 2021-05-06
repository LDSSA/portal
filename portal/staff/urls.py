from django.urls import path

from portal.staff import views


urlpatterns = [
    path("", views.HomeView.as_view(), "home"),
    path("events", views.EventsView.as_view(), "events"),
    path("candidates", views.CandidateListView.as_view(), "candidate-list"),
    path(
        "candidates/<int:user_id>/",
        views.CandidateDetailView.as_view(),
        "candidate-detail",
    ),
    path("applications", views.ApplicationView.as_view(), "application-list"),
    path("submissions", views.SubmissionView.as_view(), "submission-list"),
    path(
        "submissions/download/<int:submission_id>",
        views.SubmissionDownloadView.as_view(),
        "submission-download",
    ),
    path(
        "submissions/download-feedback/<int:submission_id>",
        views.SubmissionFeedbackDownloadView.as_view(),
        "submission-feedback-download",
    ),
    path("selections/", views.SelectionListView.as_view(), "selection-list"),
    path(
        "selections/draw", views.SelectionDrawView.as_view(), "selection-draw"
    ),
    path(
        "selections/reject-draw/<int:candidate_id>",
        views.SelectionRejectView.as_view(),
        "selection-reject",
    ),
    path(
        "selections/select",
        views.SelectionSelectView.as_view(),
        "selection-select",
    ),
    path("interviews", views.InterviewListView.as_view(), "interviews-list"),
    path(
        "interviews/<int:user_id>",
        views.InterviewDetailView.as_view(),
        "interview-detail",
    ),
    path("payments", views.PaymentListView.as_view(), "payment-list"),
    path(
        "payments/<int:user_id>",
        views.PaymentDetailView.as_view(),
        "payment-detail",
    ),
    path(
        "payments/<int:user_id>/reset",
        views.PaymentResetView.as_view(),
        "payment-reset",
    ),
    path("exports", views.ExportView, "export"),
    path("export-candidates", views.ExportCandidatesView, "export-candidates"),
]
