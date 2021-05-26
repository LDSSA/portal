from datetime import datetime, timezone
from typing import Any, Dict

from django.conf import settings
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.http.response import FileResponse
from django.shortcuts import redirect
from django.template import loader
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, View
from constance import config
from rest_framework.settings import import_from_string

from portal.applications.domain import Domain
from portal.applications.domain import Status
from portal.applications.models import (
    Application,
    Challenge,
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


class CandidateBeforeCodingTestView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/before_coding_test.html"

    def get_context_data(self, **kwargs):
        ctx = build_context(self.request.user, {
            "coding_test_duration_hours": config.ADMISSIONS_CODING_TEST_DURATION
            / 60,
            "coding_test_subtype": SubmissionTypes.coding_test,})
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        application = Application.objects.get(user=request.user)
        if application.coding_test_started_at is None:
            application.coding_test_started_at = datetime.now(timezone.utc)
            application.save()

        return HttpResponseRedirect("/candidate/coding-test")


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


class CodingTestView(AdmissionsCandidateViewMixin, TemplateView):

    def get(self, request, *args, **kwargs):
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


class AssignmentDownloadView(AdmissionsCandidateViewMixin, TemplateView):
    def get(self, request, *args, **kwargs):
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

        obj = Challenge.objects.get(code=assignment_id)
        return FileResponse(obj.file)


class SluView(AdmissionsCandidateViewMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if not applications_are_open():
            return HttpResponseRedirect("/candidate/home")
        application, _ = Application.objects.get_or_create(user=request.user)
        submission_type_ = getattr(SubmissionTypes, submission_type)
        ctx = build_context(
            request.user, submission_view_ctx(application, submission_type_)
        )
        template = loader.get_template("./candidate_templates/slu.html")
        return HttpResponse(template.render(ctx, request))


class SubmissionView(generic.View):

    # TODO
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return FileResponse(obj.doc)

    # TODO
    def post(self, request, *args, **kwargs):
        # Send to grading
        submission_type = kwargs.get('submission_type')
        submission_type_ = getattr(SubmissionTypes, submission_type)

        # TODO grading!
        grading_fcn = import_from_string(settings.GRADING_FCN, "GRADING_FCN")
        grading_fcn(request.user, None)

        # TODO file from form
        application = Application.objects.get(user=request.user)
        sub = Submission(
            file=request.FILE['file'],
            # TODO score
            # score=submission_result.score,
            # TODO feedback
            # feedback_location=submission_result.feedback_s3_key,
        )
        Domain.add_submission(application, submission_type_, sub)

        if submission_type == SubmissionTypes.coding_test.uname:
            return HttpResponseRedirect("/candidate/coding-test")
        return HttpResponseRedirect(f"/candidate/slu/{submission_type}")


class SubmissionDownloadView(generic.DetailView):
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return FileResponse(obj.doc)


class SubmissionFeedbackDownloadView(generic.DetailView):
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return FileResponse(obj.doc)


class CandidatePaymentView(generic.DetailView):

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
        try:
            selection = request.user.selection
        except Selection.DoesNotExist:
            raise Http404
        SelectionDomain.manual_update_status(
            selection, SelectionStatus.TO_BE_ACCEPTED, request.user
        )
        return HttpResponseRedirect("/candidate/payment")


# TODO permissions
class SelectionDocumentView(generic.DetailView):
    model = SelectionDocument
    queryset = SelectionDocument.objects.order_by("pk")
    document_type = None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return FileResponse(obj.doc)

    # TODO
    def post(self, request, *args, **kwargs):
        document = SelectionDocument(
            file_location=upload_key_unique, 
            doc_type=self.document_type

        )
        selection = request.user.selection
        pass

    # TODO Redirect after post
    # def get_success_url(self):
    #     return reverse("hackathons:instructor-hackathon-detail", args=(self.object.pk,)
    #     )