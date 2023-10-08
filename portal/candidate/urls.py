from django.urls import path  # noqa: D100

from portal.candidate import views

app_name = "candidate"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("contact", views.ContactView.as_view(), name="contact"),
    path(
        "code-of-conduct",
        views.CodeOfConductView.as_view(),
        name="codeofconduct",
    ),
    path("scholarship", views.ScholarshipView.as_view(), name="scholarship"),
    path(
        "before-coding-test",
        views.CandidateBeforeCodingTestView.as_view(),
        name="before-coding-test",
    ),
    path(
        "coding-test",
        views.CodingTestView.as_view(),
        name="coding-test",
    ),
    path("slu/<slug:pk>", views.SluView.as_view(), name="slu"),
    path(
        "assignment-download/<slug:pk>/",
        views.AssignmentDownloadView.as_view(),
        name="assignment-download",
    ),
    path(
        "submissions/upload/<slug:pk>",
        views.SubmissionView.as_view(),
        name="submission-upload",
    ),
    path(
        "submission/<int:pk>",
        views.SubmissionDownloadView.as_view(),
        name="submission-download",
    ),
    path(
        "submission/feedback/<int:pk>",
        views.SubmissionFeedbackDownloadView.as_view(),
        name="submissions-feedback-download",
    ),
    path("payment", views.CandidatePaymentView.as_view(), name="payment"),
    path(
        "payment/download-document/<int:pk>",
        views.SelectionDocumentDownloadView.as_view(),
        name="payment-document-download",
    ),
    path(
        "payment/upload-payment-proof",
        views.SelectionDocumentUploadView.as_view(document_type="payment_proof"),
        name="payment-proof-upload",
    ),
    path(
        "payment/upload-student-id",
        views.SelectionDocumentUploadView.as_view(document_type="student_id"),
        name="student-id-upload",
    ),
]
