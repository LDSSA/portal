import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from constance import config
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
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
from portal.admissions.policy import academy_open, registration_changes_open
from portal.applications.domain import Domain, Status
from portal.applications.models import (
    Application,
    Challenge,
    Submission,
)
from portal.candidate.domain import Domain as CandidateDomain
from portal.candidate.domain import notebook_to_html
from portal.candidate.forms import (
    AcademyTypeForm,
    CodeOfConductForm,
    DocumentUploadForm,
    ScholarshipForm,
)
from portal.selection.enrollment import (
    complete_registration,
    record_registration_step,
    submit_payment,
    upload_document,
)
from portal.selection.models import Selection, SelectionDocument
from portal.selection.payment import can_be_updated
from portal.selection.queries import SelectionDocumentQueries
from portal.selection.status import SelectionStatus
from portal.users.views import (
    AdmissionsCandidateViewMixin,
    AdmissionsViewMixin,
    CandidateAcceptedCoCMixin,
    ExamCandidateRequiredMixin,
)

logger = logging.getLogger(__name__)


class HomeView(AdmissionsCandidateViewMixin, TemplateView):
    template_name = "candidate_templates/home.html"

    def get_template_names(self):
        if not self.request.user.admissions_requires_exam:
            return ["candidate_templates/home_no_exam.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        state = CandidateDomain.get_candidate_state(self.request.user)
        if not self.request.user.admissions_requires_exam:
            return super().get_context_data(
                state=state,
                selection=Selection.objects.filter(user=self.request.user).first(),
                selection_status_values=SelectionStatus,
                first_name=self.request.user.name.split(" ")[0],
                registration_open=registration_changes_open(self.request.user),
                academy_access_open=academy_open(self.request.user),
                **kwargs,
            )

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


class RegistrationStepView(AdmissionsCandidateViewMixin, generic.FormView):
    step = None
    value_field = None

    def form_valid(self, form):
        value = form.cleaned_data[self.value_field]
        if self.step == "scholarship":
            value = value == "yes"
        try:
            record_registration_step(self.request.user, self.step, value)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("admissions:candidate:home")


class CodeOfConductView(RegistrationStepView):
    template_name = "candidate_templates/code_of_conduct.html"
    form_class = CodeOfConductForm
    step = "coc"
    value_field = "accepted"


class ScholarshipView(CandidateAcceptedCoCMixin, RegistrationStepView):
    template_name = "candidate_templates/scholarship.html"
    form_class = ScholarshipForm
    step = "scholarship"
    value_field = "decision"


class AcademyTypeView(CandidateAcceptedCoCMixin, RegistrationStepView):
    template_name = "candidate_templates/academy_type.html"
    form_class = AcademyTypeForm
    step = "academy_type"
    value_field = "academy_type"

    def get_initial(self):
        return {"academy_type": self.request.user.academy_type_preference}


class CompleteRegistrationView(AdmissionsCandidateViewMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if request.user.admissions_requires_exam:
            raise Http404
        try:
            if complete_registration(request.user) is None:
                messages.error(
                    request,
                    "Complete your profile and all three steps while registration is open.",
                )
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        return redirect("admissions:candidate:home")


class CandidateBeforeCodingTestView(
    ExamCandidateRequiredMixin, AdmissionsCandidateViewMixin, TemplateView
):
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


class CandidateConfirmationCodingTestView(
    ExamCandidateRequiredMixin, AdmissionsCandidateViewMixin, TemplateView
):
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
        now = datetime.now(timezone.utc)
        if (
            not config.ADMISSIONS_APPLICATIONS_START
            <= now
            < config.ADMISSIONS_SELECTION_START
        ):
            return HttpResponseBadRequest("The admission tests are not open.")
        with transaction.atomic():
            application = Application.objects.select_for_update().get(user=request.user)
            if application.coding_test_started_at is None:
                application.coding_test_started_at = now
                application.save(update_fields=["coding_test_started_at"])

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


class CodingTestView(
    ExamCandidateRequiredMixin, AdmissionsCandidateViewMixin, TemplateView
):
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
        if application.coding_test_started_at is None:  # this should probably go
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


class AssignmentDownloadView(
    ExamCandidateRequiredMixin, AdmissionsViewMixin, TemplateView
):
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
            and application.coding_test_started_at is None  # this has to change
        ):
            raise Http404

        # download_counter_var = {"coding_test":application.coding_test_downloaded,
        #                        "slu01":application.slu01_downloaded,
        #                        "slu02":application.slu02_downloaded,
        #                        "slu03":application.slu03_downloaded}

        obj = Challenge.objects.get(code=assignment_id)
        try:
            # download_counter_var[assignment_id]=+1
            return FileResponse(obj.file)
        except ValueError as exc:
            raise Http404 from exc


class SluView(ExamCandidateRequiredMixin, AdmissionsCandidateViewMixin, TemplateView):
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


class SubmissionView(
    ExamCandidateRequiredMixin, AdmissionsCandidateViewMixin, generic.View
):
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


class SubmissionDownloadView(
    ExamCandidateRequiredMixin, AdmissionsViewMixin, generic.DetailView
):
    queryset = Submission.objects.filter(
        user__admissions_mode="exam", application__user__admissions_mode="exam"
    )

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


class SubmissionFeedbackDownloadView(
    ExamCandidateRequiredMixin, AdmissionsViewMixin, generic.DetailView
):
    queryset = Submission.objects.filter(
        user__admissions_mode="exam", application__user__admissions_mode="exam"
    )

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

        if selection.payment_value is None:
            return redirect("admissions:candidate:home")

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

    def post(self, request, *args, **kwargs):
        try:
            submit_payment(request.user)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        return redirect("admissions:candidate:payment")


class SelectionDocumentDownloadView(AdmissionsViewMixin, generic.DetailView):
    model = SelectionDocument
    queryset = SelectionDocument.objects.order_by("pk")

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(selection__user=self.request.user)

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


class SelectionDocumentUploadView(AdmissionsCandidateViewMixin, generic.DetailView):
    model = SelectionDocument
    queryset = SelectionDocument.objects.order_by("pk")
    document_type = None

    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                upload_document(
                    request.user, form.cleaned_data["file"], self.document_type
                )
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
        else:
            messages.error(request, "Choose a non-empty document to upload.")
        return redirect("admissions:candidate:payment")
