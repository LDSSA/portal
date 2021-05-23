from datetime import datetime, timezone
from typing import Any, Dict

from django.conf import settings
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import redirect
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, View
from constance import config

from portal.applications.domain import Domain
from portal.applications.domain import Status
from portal.applications.models import (
    Application,
    Submission,
    SubmissionType,
    SubmissionTypes,
)
from portal.candidate.domain import Domain
from portal.candidate.helpers import applications_are_open, build_context
from portal.candidate.helpers import build_context

from portal.selection.domain import SelectionDomain
from portal.selection.models import Selection, SelectionDocument
from portal.selection.payment import add_document, can_be_updated
from portal.selection.queries import SelectionDocumentQueries
from portal.selection.status import SelectionStatus
from portal.users.views import AdmissionsCandidateViewMixin, CandidateAcceptedCoCMixin


class HomeView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/home.html"

    def get_context_data(self, **kwargs):
        state = Domain.get_candidate_state(self.request.user)

        # the action_point is the first open section in the steps accordion
        # accordion_enabled_status say whether each accordion section should be enabled
        accordion_enabled_status = {
            "accepted_coc": False,
            "decided_scholarship": False,
            "admission_test": False,
            "selection_results": False,
            "payment": False,
        }

        if not state.accepted_coc:
            action_point = "accepted_coc"
            accordion_enabled_status["accepted_coc"] = True

        elif not state.decided_scholarship:
            action_point = "decided_scholarship"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True

        elif (
            state.application_status != Status.passed
            or state.selection_status is None
        ):
            action_point = "admission_test"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["admission_test"] = True

        elif (
            state.selection_status is not None
            and state.selection_status
            not in SelectionStatus.SELECTION_POSITIVE_STATUS
        ):
            action_point = "selection_results"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["admission_test"] = True
            accordion_enabled_status["selection_results"] = True

        else:
            action_point = "payment"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["admission_test"] = True
            accordion_enabled_status["selection_results"] = True
            accordion_enabled_status["payment"] = True

        first_name = self.request.user.name.split(" ")[0]

        ctx = build_context(
            self.request.user,
            {
                "user": self.request.user,
                "state": state,
                "selection_status_values": SelectionStatus,
                "action_point": action_point,
                "first_name": first_name,
                "is_applications_open": datetime.now(timezone.utc)
                >= config.ADMISSIONS_APPLICATIONS_OPENING_DATE,
                "applications_open_datetime": config.ADMISSIONS_APPLICATIONS_OPENING_DATE.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "applications_close_datetime": config.ADMISSIONS_APPLICATIONS_CLOSING_DATE.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "applications_close_date": config.ADMISSIONS_APPLICATIONS_CLOSING_DATE.strftime(
                    "%Y-%m-%d"
                ),
                "coding_test_duration": config.ADMISSIONS_CODING_TEST_DURATION
                / 60,
                "accordion_enabled_status": accordion_enabled_status,
            },
        )
        return super().get_context_data(**ctx)


class ContactView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/contactus.html"

    def get_context_data(self, **kwargs):
        ctx = build_context(self.request.user)
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_url = f"{get_url(request)}/staff/candidates/{user.id}/"
        message = request.POST["message"]
        try:
            user_name = user.profile.full_name
        except Profile.DoesNotExist:
            user_name = "-"

        settings.email_client.send_contact_us_email(
            from_email=user.email,
            user_name=user_name,
            user_url=user_url,
            message=message,
        )
        user.save()

        # TODO get_sucess_url
        template = loader.get_template(
            "./candidate_templates/contactus-success.html"
        )
        ctx = build_context(request.user)
        return HttpResponse(template.render(ctx, request))


class CodeOfConductView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/code_of_conduct.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        ctx = build_context(
            user, {"code_of_conduct_accepted": user.code_of_conduct_accepted}
        )
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        user = request.user
        user.code_of_conduct_accepted = True
        user.save()
        return redirect("admissions:candidate:home")


class ScholarshipView(AdmissionsCandidateViewMixin, CandidateAcceptedCoCMixin, TemplateView):
    template_name = "candidate_templates/scholarship.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        ctx = build_context(
            self.request.user,
            {
                "decision_made": user.applying_for_scholarship is not None,
                "applying_for_scholarship": user.applying_for_scholarship,
            },
        )
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        user = request.user
        user.applying_for_scholarship = request.POST["decision"] == "yes"
        user.save()
        return redirect("admissions:candidate:home")


@require_http_methods(["GET", "POST"])
def candidate_before_coding_test_view(request: HttpRequest) -> HttpResponse:
    if not applications_are_open():
        return HttpResponseRedirect("/candidate/home")

    if request.method == "GET":
        template = loader.get_template(
            "./candidate_templates/before_coding_test.html"
        )
        ctx = {
            **build_context(request.user),
            "coding_test_duration_hours": config.ADMISSIONS_CODING_TEST_DURATION
            / 60,
            "coding_test_subtype": SubmissionTypes.coding_test,
        }
        return HttpResponse(template.render(ctx, request))

    application = Application.objects.get(user=request.user)
    if application.coding_test_started_at is None:
        application.coding_test_started_at = datetime.now(timezone.utc)
        application.save()

    return HttpResponseRedirect("/candidate/coding-test")


@require_http_methods(["GET"])
def candidate_coding_test_view(request: HttpRequest) -> HttpResponse:
    if not applications_are_open():
        return HttpResponseRedirect("/candidate/home")

    application, _ = Application.objects.get_or_create(user=request.user)
    if application.coding_test_started_at is None:
        return HttpResponseRedirect("/candidate/before-coding-test")

    submission_type_ = SubmissionTypes.coding_test
    sub_view_ctx = {
        **submission_view_ctx(application, submission_type_),
        "coding_test_duration_hours": config.ADMISSIONS_CODING_TEST_DURATION
        / 60,
    }
    ctx = build_context(request.user, sub_view_ctx)
    template = loader.get_template("./candidate_templates/coding_test.html")
    return HttpResponse(template.render(ctx, request))


@require_http_methods(["GET"])
def candidate_assignment_download_view(request: HttpRequest) -> HttpResponse:
    try:
        assignment_id = request.GET["assignment_id"]
    except Exception:
        raise Http404

    application = Application.objects.get(user=request.user)
    if (
        assignment_id == SubmissionTypes.coding_test.uname
        and application.coding_test_started_at is None
    ):
        raise Http404

    key = Domain.get_candidate_release_zip(assignment_id)
    url = interface.storage_client.get_attachment_url(
        key, content_type="application/zip"
    )
    return HttpResponseRedirect(url)


@require_http_methods(["GET"])
def candidate_slu_view(
    request: HttpRequest, submission_type: str
) -> HttpResponse:
    if not applications_are_open():
        return HttpResponseRedirect("/candidate/home")
    application, _ = Application.objects.get_or_create(user=request.user)
    submission_type_ = getattr(SubmissionTypes, submission_type)
    ctx = build_context(
        request.user, submission_view_ctx(application, submission_type_)
    )
    template = loader.get_template("./candidate_templates/slu.html")
    return HttpResponse(template.render(ctx, request))


@require_http_methods(["POST"])
def candidate_submission_upload_view(
    request: HttpRequest, submission_type: str
) -> HttpResponse:
    submission_type_ = getattr(SubmissionTypes, submission_type)

    file = request.FILES["file"]
    now_str = datetime.now(timezone.utc).strftime("%m_%d_%Y__%H_%M_%S")
    upload_key = (
        f"{submission_type_.uname}/{request.user.uuid}/{file.name}@{now_str}"
    )
    interface.storage_client.save(upload_key, file)

    submission_result = interface.grader_client.grade(
        assignment_id=submission_type_.uname,
        user_uuid=request.user.uuid,
        submission_s3_bucket=settings.STORAGE_BUCKET,
        submission_s3_key=upload_key,
    )

    application = Application.objects.get(user=request.user)
    sub = Submission(
        file_location=upload_key,
        score=submission_result.score,
        feedback_location=submission_result.feedback_s3_key,
    )
    Domain.add_submission(application, submission_type_, sub)

    if submission_type == SubmissionTypes.coding_test.uname:
        return HttpResponseRedirect("/candidate/coding-test")
    return HttpResponseRedirect(f"/candidate/slu/{submission_type}")


def submission_view_ctx(
    application: Application, submission_type: SubmissionType
) -> Dict[str, Any]:
    return {
        "submission_type": submission_type,
        "status": Domain.get_sub_type_status(
            application, submission_type
        ).name,
        "submissions_closes_at": Domain.get_end_date(
            application, submission_type
        ).strftime("%Y-%m-%d %H:%M"),
        "best_score": Domain.get_best_score(application, submission_type),
        "download_enabled": Domain.can_add_submission(
            application, submission_type
        ),
        "upload_enabled": Domain.can_add_submission(
            application, submission_type
        ),
        "submissions": Submission.objects.filter(
            application=application, submission_type=submission_type.uname
        ).order_by("-updated_at"),
        "coding_test_started_at_ms": int(
            application.coding_test_started_at.timestamp() * 1000
        )
        if application.coding_test_started_at is not None
        else None,
    }


@require_http_methods(["GET"])
def candidate_submission_download_view(
    request: HttpRequest, submission_type: str, submission_id: int
) -> HttpResponse:
    try:
        submission: Submission = Submission.objects.get(
            id=submission_id,
            submission_type=submission_type,
            application=request.user.application,
        )
    except Submission.DoesNotExist:
        raise Http404
    url = interface.storage_client.get_attachment_url(
        submission.file_location, content_type="application/vnd.jupyter"
    )

    return HttpResponseRedirect(url)


@require_http_methods(["GET"])
def candidate_submission_feedback_download_view(
    request: HttpRequest, submission_type: str, submission_id: int
) -> HttpResponse:
    try:
        submission: Submission = Submission.objects.get(
            id=submission_id,
            submission_type=submission_type,
            application=request.user.application,
        )
    except Submission.DoesNotExist:
        raise Http404
    url = interface.storage_client.get_url(
        submission.feedback_location, content_type="text/html"
    )

    return HttpResponseRedirect(url)


def _get_candidate_payment_view(request: HttpRequest) -> HttpResponse:
    try:
        selection = request.user.selection
    except Selection.DoesNotExist:
        raise Http404

    payment_proofs = SelectionDocumentQueries.get_payment_proof_documents(
        selection
    )
    student_ids = SelectionDocumentQueries.get_student_id_documents(selection)

    template = loader.get_template("./candidate_templates/payment.html")

    context = {
        "s": selection,
        "selection_status": SelectionStatus,
        "can_update": can_be_updated(selection),
        "profile": request.user.profile,
        "payment_proofs": payment_proofs,
        "student_ids": student_ids,
    }
    context = build_context(request.user, context)

    return HttpResponse(template.render(context, request))


def _post_candidate_payment_view(request: HttpRequest) -> HttpResponse:
    try:
        selection = request.user.selection
    except Selection.DoesNotExist:
        raise Http404
    SelectionDomain.manual_update_status(
        selection, SelectionStatus.TO_BE_ACCEPTED, request.user
    )
    return HttpResponseRedirect("/candidate/payment")


@require_http_methods(["GET", "POST"])
def candidate_payment_view(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return _get_candidate_payment_view(request)
    return _post_candidate_payment_view(request)


@require_http_methods(["GET"])
def candidate_document_download_view(
    request: HttpRequest, document_id: int
) -> HttpResponse:
    try:
        selection = request.user.selection
        document = SelectionDocument.objects.get(
            selection=selection, id=document_id
        )
    except (Selection.DoesNotExist, SelectionDocument.DoesNotExist):
        raise Http404
    url = interface.storage_client.get_attachment_url(document.file_location)

    return HttpResponseRedirect(url)


@require_http_methods(["POST"])
def candidate_payment_proof_upload_view(request: HttpRequest) -> HttpResponse:
    return _candidate_document_upload(request, document_type="payment_proof")


@require_http_methods(["POST"])
def candidate_student_id_upload_view(request: HttpRequest) -> HttpResponse:
    return _candidate_document_upload(request, document_type="student_id")


def _candidate_document_upload(
    request: HttpRequest, document_type: str
) -> HttpResponse:
    f = request.FILES["file"]
    upload_key = f"payments/{document_type}/{request.user.uuid}/{f.name}"
    upload_key_unique = interface.storage_client.key_append_uuid(upload_key)

    interface.storage_client.save(upload_key_unique, f)

    document = SelectionDocument(
        file_location=upload_key_unique, doc_type=document_type
    )
    selection = request.user.selection
    add_document(selection, document)

    return HttpResponseRedirect("/candidate/payment")
