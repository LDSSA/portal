from django.urls import path

from portal.candidate import views


app_name = "candidate"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("contact", views.ContactView.as_view(), name="contact"),
    path(
        "code-of-conduct", views.CodeOfConductView.as_view(), name="codeofconduct"
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
    path(
        "assignment-download",
        views.AssignmentDownloadView.as_view(),
        name="assignment-download",
    ),
    path(
        "slu/<slug:submission_type>", views.SluView, name="slu"
    ),
    path(
        "submissions/upload/<slug:submission_type>",
        views.SubmissionView.as_view(),
        name="submissions-upload",
    ),
    path(
        "submission/<slug:submission_type>/<int:submission_id>",
        views.SubmissionDownloadView.as_view(),
        name="submission-download",
    ),
    path(
        "submission/feedback/<slug:submission_type>/<int:submission_id>",
        views.SubmissionFeedbackDownloadView.as_view(),
        name="submissions-feedback-download",
    ),
    path("payment", views.CandidatePaymentView, name="payment"),
    path(
        "payment/download-document/<int:pk>",
        views.SelectionDocumentView.as_view(),
        name="payment-document-download",
    ),
    path(
        "payment/upload-payment-proof",
        views.SelectionDocumentView.as_view(document_type='payment_proof'),
        name="payment-proof-upload",
    ),
    path(
        "payment/upload-student-id",
        views.SelectionDocumentView.as_view(document_type='student_id'),
        name="student-id-upload",
    ),
]
