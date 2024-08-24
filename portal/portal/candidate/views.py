import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from constance import config
from django.conf import settings
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
)
from django.http.response import FileResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView
from rest_framework.settings import import_string

from portal.admissions import emails
from portal.applications.domain import Domain, Status
from portal.applications.models import (
    Application,
    Challenge,
    Submission,
)
from portal.candidate.domain import Domain as CandidateDomain
from portal.candidate.domain import notebook_to_html
from portal.selection.domain import SelectionDomain
from portal.selection.models import Selection, SelectionDocument
from portal.selection.payment import add_document, can_be_updated
from portal.selection.queries import SelectionDocumentQueries
from portal.selection.status import SelectionStatus
from portal.users.models import TicketType
from portal.users.views import (
    AdmissionsCandidateViewMixin,
    AdmissionsViewMixin,
    CandidateAcceptedCoCMixin,
)

logger = logging.getLogger(__name__)


class HomeView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/home.html"

    def get_context_data(self, **kwargs):
        state = CandidateDomain.get_candidate_state(self.request.user)

        # the action_point is the first open section in the steps accordion
        # accordion_enabled_status say whether each accordion section should be enabled
        accordion_enabled_status = {
            "accepted_coc": False,
            "decided_scholarship": False,
            "decided_academy_type": False,
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

        elif not state.academy_type:
            action_point = "decided_academy_type"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["decided_academy_type"] = True

        elif (
            state.application_status != Status.passed or state.selection_status is None
        ):
            action_point = "admission_test"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["decided_academy_type"] = True
            accordion_enabled_status["admission_test"] = True

        elif (
            state.selection_status is not None
            and state.selection_status not in SelectionStatus.SELECTION_POSITIVE_STATUS
        ):
            action_point = "selection_results"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["decided_academy_type"] = True
            accordion_enabled_status["admission_test"] = True
            accordion_enabled_status["selection_results"] = True

        else:
            action_point = "payment"
            accordion_enabled_status["accepted_coc"] = True
            accordion_enabled_status["decided_scholarship"] = True
            accordion_enabled_status["decided_academy_type"] = True
            accordion_enabled_status["admission_test"] = True
            accordion_enabled_status["selection_results"] = True
            accordion_enabled_status["payment"] = True

        first_name = self.request.user.name.split(" ")[0]

        ctx = {
            "user": self.request.user,
            "state": state,
            "selection_status_values": SelectionStatus,
            "action_point": action_point,
            "first_name": first_name,
            "portal_status": config.PORTAL_STATUS,
            "applications_open_datetime": config.ADMISSIONS_APPLICATIONS_START.strftime(
                "%Y-%m-%d %H:%M",
            ),
            "applications_close_datetime": config.ADMISSIONS_SELECTION_START.strftime(
                "%Y-%m-%d %H:%M",
            ),
            "applications_close_date": config.ADMISSIONS_SELECTION_START.strftime(
                "%Y-%m-%d"
            ),
            "coding_test_duration": str(config.ADMISSIONS_CODING_TEST_DURATION),
            "accordion_enabled_status": accordion_enabled_status,
        }
        return super().get_context_data(**ctx)


class ContactView(AdmissionsCandidateViewMixin, TemplateView):
    """Send email to site admins."""

    template_name = "candidate_templates/contactus.html"

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = request.user
        user_url = reverse("admissions:staff:candidate-detail", args=(user.pk,))
        message = request.POST["message"]
        user_name = user.name

        emails.send_contact_us_email(
            from_email=user.email,
            user_name=user_name,
            user_url=urljoin(settings.BASE_URL, user_url),
            message=message,
        )
        user.save()

        template = loader.get_template("./candidate_templates/contactus-success.html")
        return HttpResponse(template.render({}, request))


class CodeOfConductView(AdmissionsCandidateViewMixin, TemplateView):
    """View and accept code of conduct."""

    template_name = "candidate_templates/code_of_conduct.html"

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = request.user
        user.code_of_conduct_accepted = True
        user.save()
        return redirect("admissions:candidate:home")


class ScholarshipView(
    AdmissionsCandidateViewMixin, CandidateAcceptedCoCMixin, TemplateView
):
    """Read scholarship conditions and chose to apply."""

    template_name = "candidate_templates/scholarship.html"

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = request.user
        user.applying_for_scholarship = request.POST["decision"] == "yes"
        if user.applying_for_scholarship:
            user.ticket_type = TicketType.scholarship
        user.save()
        return redirect("admissions:candidate:home")


class AcademyTypeView(
    AdmissionsCandidateViewMixin, CandidateAcceptedCoCMixin, TemplateView
):
    """Choose academy type preference."""

    template_name = "candidate_templates/academy_type.html"

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = request.user
        user.academy_type_preference = request.POST["academy_type"]
        user.save()
        return redirect("admissions:candidate:home")


class CandidateBeforeCodingTestView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/before_coding_test.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "coding_test_duration_hours": str(
                config.ADMISSIONS_CODING_TEST_DURATION.total_seconds() / 3600,
            ),
            "coding_test_subtype": Challenge.objects.get(code="coding_test"),
        }
        return super().get_context_data(**ctx)

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        Application.objects.get(user=request.user)

        return HttpResponseRedirect(
            reverse("admissions:candidate:confirmation-coding-test")
        )


class CandidateConfirmationCodingTestView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/confirmation_coding_test.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "coding_test_duration_hours": str(
                config.ADMISSIONS_CODING_TEST_DURATION.total_seconds() / 3600,
            ),
            "coding_test_subtype": Challenge.objects.get(code="coding_test"),
        }
        return super().get_context_data(**ctx)

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        application = Application.objects.get(user=request.user)
        if application.coding_test_started_at is None:
            application.coding_test_started_at = datetime.now(timezone.utc)
            application.save()

        return HttpResponseRedirect(reverse("admissions:candidate:coding-test"))


def submission_view_ctx(application, challenge) -> dict[str, Any]:
    return {
        "challenge": challenge,
        "status": Domain.get_sub_type_status(application, challenge).name,
        "submissions_closes_at": Domain.get_end_date(application, challenge).strftime(
            "%Y-%m-%d %H:%M",
        ),
        "best_score": Domain.get_best_score(application, challenge),
        "download_enabled": Domain.can_add_submission(application, challenge),
        "upload_enabled": Domain.can_add_submission(application, challenge),
        "submissions": Submission.objects.filter(
            application=application, unit=challenge
        ).order_by(
            "-updated_at",
        ),
        "coding_test_started_at_ms": int(
            application.coding_test_started_at.timestamp() * 1000
        )
        if application.coding_test_started_at is not None
        else None,
    }


class CodingTestView(AdmissionsCandidateViewMixin, TemplateView):
    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        if (
            config.PORTAL_STATUS
            not in settings.ADMISSIONS_APPLICATIONS_STARTED_STATUSES
        ):
            return HttpResponseRedirect(reverse("home"))

        application, _ = Application.objects.get_or_create(user=request.user)
        if application.coding_test_started_at is None:
            return HttpResponseRedirect(
                reverse("admissions:candidate:before-coding-test")
            )

        submission_type_ = Challenge.objects.get(code="coding_test")
        ctx = {
            **submission_view_ctx(application, submission_type_),
            "coding_test_duration_hours": str(
                config.ADMISSIONS_CODING_TEST_DURATION.total_seconds() / 3600,
            ),
        }
        template = loader.get_template("./candidate_templates/coding_test.html")
        return HttpResponse(template.render(ctx, request))


class AssignmentDownloadView(AdmissionsViewMixin, TemplateView):
    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        assignment_id = kwargs.get("pk")
        application = Application.objects.get(user=request.user)
        if (
            assignment_id == "coding_test"
            and application.coding_test_started_at is None
        ):
            raise Http404

        obj = Challenge.objects.get(code=assignment_id)
        try:
            return FileResponse(obj.file)
        except ValueError as exc:
            raise Http404 from exc


class SluView(AdmissionsCandidateViewMixin, TemplateView):
    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        if kwargs["pk"] == "coding_test":
            raise Http404

        if (
            config.PORTAL_STATUS
            not in settings.ADMISSIONS_APPLICATIONS_STARTED_STATUSES
        ):
            return HttpResponseRedirect(reverse("home"))

        application, _ = Application.objects.get_or_create(user=request.user)
        challenge = Challenge.objects.get(code=kwargs["pk"])
        ctx = submission_view_ctx(application, challenge)
        template = loader.get_template("./candidate_templates/slu.html")
        return HttpResponse(template.render(ctx, request))


class SubmissionView(AdmissionsCandidateViewMixin, generic.View):
    """Submit challenges."""

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        # Send to grading
        pk = kwargs.get("pk")
        challenge = Challenge.objects.get(code=pk)

        if not Domain.can_add_submission(request.user.application, challenge):
            return HttpResponseBadRequest("Can't add submission")

        sub = Submission.objects.create(
            application=request.user.application,
            user=request.user,
            unit=challenge,
            notebook=request.FILES["file"],
        )
        grading = import_string(settings.GRADING_ADMISSIONS_CLASS)
        grading(grade=sub).run_grading()

        if pk == "coding_test":
            return HttpResponseRedirect(reverse("admissions:candidate:coding-test"))
        return HttpResponseRedirect(reverse("admissions:candidate:slu", args=(pk,)))


class SubmissionDownloadView(AdmissionsViewMixin, generic.DetailView):
    queryset = Submission.objects.all()

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        obj = self.get_object()
        try:
            return FileResponse(obj.notebook)
        except ValueError as exc:
            raise Http404 from exc


class SubmissionFeedbackDownloadView(AdmissionsViewMixin, generic.DetailView):
    queryset = Submission.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        obj = self.get_object()
        try:
            return HttpResponse(notebook_to_html(obj.feedback.read()))
        except ValueError as exc:
            raise Http404 from exc


class CandidatePaymentView(AdmissionsCandidateViewMixin, generic.DetailView):
    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        try:
            selection = request.user.selection
        except Selection.DoesNotExist as exc:
            raise Http404 from exc

        payment_proofs = SelectionDocumentQueries.get_payment_proof_documents(selection)
        student_ids = SelectionDocumentQueries.get_student_id_documents(selection)

        template = loader.get_template("./candidate_templates/payment.html")

        context = {
            "s": selection,
            "selection_status": SelectionStatus,
            "can_update": can_be_updated(selection),
            "profile": request.user,
            "payment_proofs": payment_proofs,
            "student_ids": student_ids,
        }
        return HttpResponse(template.render(context, request))

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        try:
            selection = request.user.selection
        except Selection.DoesNotExist as exc:
            raise Http404 from exc
        SelectionDomain.manual_update_status(
            selection,
            SelectionStatus.TO_BE_ACCEPTED,
            request.user,
        )
        return HttpResponseRedirect(reverse("admissions:candidate:payment"))


class SelectionDocumentDownloadView(AdmissionsViewMixin, generic.DetailView):
    model = SelectionDocument
    queryset = SelectionDocument.objects.order_by("pk")

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(selection=self.request.user.selection)

    def get(
        self,
        request,
        *args,
        **kwargs,
    ):
        obj = self.get_object()
        try:
            return FileResponse(obj.doc)
        except ValueError as exc:
            raise Http404 from exc


class SelectionDocumentUploadView(AdmissionsViewMixin, generic.DetailView):
    model = SelectionDocument
    queryset = SelectionDocument.objects.order_by("pk")
    document_type = None

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        add_document(
            request.user.selection,
            document=request.FILES["file"],
            document_type=self.document_type,
        )
        return HttpResponseRedirect(reverse("admissions:candidate:payment"))
