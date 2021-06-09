import csv
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Any, Dict

from dateutil import tz
from constance import config
from django.http import (
    HttpResponseServerError,
    Http404,
)
from django.http.response import FileResponse, HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.urls import reverse

from portal.admissions import emails
from portal.applications.domain import Domain as ApplicationDomain, Status
from portal.applications.models import Submission, Application, Challenge
from portal.selection.domain import SelectionDomain
from portal.selection.draw import default_draw_params, draw, reject_draw
from portal.selection.logs import get_selection_logs
from portal.selection.models import Selection
from portal.selection.queries import SelectionQueries
from portal.selection.payment import (
    add_note,
    load_payment_data,
    can_be_updated,
)
from portal.selection.select import select
from portal.selection.status import SelectionStatus
from portal.staff.domain import Events, EventsException
from portal.users.models import User, Gender, TicketType
from portal.users.views import AdmissionsStaffViewMixin
from portal.staff.export import get_all_candidates

logger = getLogger(__name__)


DATETIME_FMT = "%d/%m/%Y %H:%M:%S"
TIME_FMT = "%H:%M:%S"


class HomeView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/home.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "user": self.request.user,
            "datetime_fmt": DATETIME_FMT,
            "time_fmt": TIME_FMT,
            "datetime_flags": [
                {
                    "key": "applications_opening_date",
                    "value": config.ADMISSIONS_APPLICATIONS_START.strftime(
                        DATETIME_FMT
                    ),
                    "label": "Challenge Submissions Opening Date",
                },
                {
                    "key": "applications_closing_date",
                    "value": config.ADMISSIONS_SELECTION_START.strftime(
                        DATETIME_FMT
                    ),
                    "label": "Challenge Submissions Closing Date",
                },
            ],
            "time_flags": [
                {
                    "key": "coding_test_duration",
                    "value": str(config.ADMISSIONS_CODING_TEST_DURATION),
                    "label": "Challenge Submissions Opening Date",
                },
            ],
            "bool_flags": [
                {
                    "key": "signups_are_open",
                    "value": config.ACCOUNT_ALLOW_REGISTRATION,
                    "label": "Signups",
                },
                {
                    "key": "accepting_payment_profs",
                    "value": config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS,
                    "label": "Payment Proof Uploads",
                },
            ],
        }
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseServerError(
                b"error updating admin variables. Only admins can update these variables"
            )

        key = request.POST["key"]

        if key == "applications_opening_date":
            date_s = request.POST["date_s"]
            opening_date = datetime.strptime(date_s, DATETIME_FMT)
            opening_date = opening_date.replace(
                tzinfo=tz.gettz("Europe/Lisbon")
            )
            if opening_date > config.ADMISSIONS_SELECTION_START:
                return HttpResponseServerError(
                    b"error setting opening date. opening date must be before closing date"
                )
            else:
                config.ADMISSIONS_APPLICATIONS_START = opening_date

        elif key == "applications_closing_date":
            date_s = request.POST["date_s"]
            closing_date = datetime.strptime(date_s, DATETIME_FMT)
            closing_date = closing_date.replace(
                tzinfo=tz.gettz("Europe/Lisbon")
            )
            if closing_date < config.ADMISSIONS_APPLICATIONS_START:
                return HttpResponseServerError(
                    b"error setting closing date. closing date must be after opening date"
                )
            else:
                config.ADMISSIONS_SELECTION_START = closing_date

        elif key == "coding_test_duration":
            duration = datetime.strptime(request.POST["date_s"], TIME_FMT)
            config.ADMISSIONS_CODING_TEST_DURATION = timedelta(
                hours=duration.hour,
                minutes=duration.minute,
                seconds=duration.second,
            )

        elif key == "signups_are_open":
            if request.POST["action"] == "open":
                config.ACCOUNT_ALLOW_REGISTRATION = True
            else:
                config.ACCOUNT_ALLOW_REGISTRATION = False

        elif key == "accepting_payment_profs":
            if request.POST["action"] == "open":
                config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS = True
            else:
                config.ADMISSIONS_ACCEPTING_PAYMENT_PROFS = False
        else:
            logger.warning(f"unknown feature flag key `{key}`.. doing nothing")

        return redirect("home")


class EventsView(AdmissionsStaffViewMixin, TemplateView):
    """Trigger application and admissions ending events"""

    template_name = "staff_templates/events.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "user": self.request.user,
            "emails": [
                {
                    "key": "applications_over",
                    "sent_to": Events.applications_are_over_sent_emails(),
                    "applicable_to": Events.applications_are_over_total_emails(),
                    "label": "End Applications",
                },
                {
                    "key": "admissions_over",
                    "sent_to": Events.admissions_are_over_sent_emails(),
                    "applicable_to": Events.admissions_are_over_total_emails(),
                    "label": "End Admissions",
                },
            ],
        }
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseServerError(
                b"error triggering event. Only admins can trigger events"
            )

        key = request.POST["key"]

        if key == "applications_over":
            try:
                Events.trigger_applications_are_over()
            except EventsException:
                return HttpResponseServerError(
                    b"error triggering event. Are you sure applications are over?"
                )

        elif key == "admissions_over":
            try:
                Events.trigger_admissions_are_over()
            except EventsException:
                return HttpResponseServerError(
                    b"error triggering event. Make sure there are no candidates in `drawn` or `selected`"
                )

        return redirect("admissions:staff:events")


class CandidateListView(AdmissionsStaffViewMixin, TemplateView):
    """Candidate list."""

    template_name = "staff_templates/candidates.html"

    def get_context_data(self, **kwargs):
        ctx = {"users": User.objects.filter(is_staff=False).order_by("email")}
        return super().get_context_data(**ctx)


class CandidateDetailView(AdmissionsStaffViewMixin, TemplateView):
    """Candidate details."""

    template_name = "staff_templates/candidate.html"

    def get_context_data(self, **kwargs):
        try:
            user = User.objects.filter(is_staff=False).get(id=kwargs["pk"])
        except User.DoesNotExist:
            raise Http404

        try:
            application = user.application
            total_submissions = Submission.objects.filter(
                application=application
            ).count()
            application_best_scores = {
                "coding_test": ApplicationDomain.get_best_score(
                    application, Challenge.objects.get(code="coding_test")
                ),
                "slu01": ApplicationDomain.get_best_score(
                    application, Challenge.objects.get(code="slu01")
                ),
                "slu02": ApplicationDomain.get_best_score(
                    application, Challenge.objects.get(code="slu02")
                ),
                "slu03": ApplicationDomain.get_best_score(
                    application, Challenge.objects.get(code="slu03")
                ),
            }
        except Application.DoesNotExist:
            total_submissions = 0
            application_best_scores = {}

        ctx = {
            "user": user,
            "total_submissions": total_submissions,
            "application_best_scores": application_best_scores,
        }
        return super().get_context_data(**ctx)


class ApplicationView(AdmissionsStaffViewMixin, TemplateView):
    """Candidate application details."""

    template_name = "staff_templates/applications.html"

    def get_context_data(self, **kwargs):
        query = Application.objects.all().order_by("user__email")

        filter_by_application_status = self.request.GET.get(
            "application_status"
        )

        applications = []
        count_by_type: Dict[Any, Any] = {
            "application": {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            "coding_test": {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            "slu01": {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            "slu02": {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            "slu03": {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
        }
        for a in query:
            application_det_status = (
                ApplicationDomain.get_application_detailed_status(a)
            )
            for sub_type, sub_status in application_det_status.items():
                count_by_type[sub_type][sub_status.name] += 1

            if (
                filter_by_application_status is not None
                and application_det_status["application"].name
                != filter_by_application_status
            ):
                continue

            applications.append(
                {
                    "ref": a,
                    "status_list": [
                        application_det_status["application"],
                        *[
                            ApplicationDomain.get_sub_type_status(
                                a, Challenge.objects.get(pk=code)
                            )
                            for code in [
                                "coding_test",
                                "slu01",
                                "slu02",
                                "slu03",
                            ]
                        ],
                    ],
                }
            )

        status_enum = {
            s.name: {
                "name": s.name,
                "value": s.value,
                "count": count_by_type["application"][s.name],
            }
            for s in Status
        }
        ctx = {
            "status_enum": status_enum,
            "applications": applications,
            "summary": count_by_type,
        }
        return super().get_context_data(**ctx)


class SubmissionView(AdmissionsStaffViewMixin, TemplateView):
    """Candidate submissions list??"""

    template_name = "staff_templates/submissions.html"

    def get_context_data(self, **kwargs):
        query = Submission.objects.all().order_by("-created_at")

        user_email = self.request.GET.get("user_email", None)
        if user_email is not None:
            query = query.filter(application__user__email__contains=user_email)
        else:
            query = query[:25]

        ctx = {
            "submissions": query.values(
                "id",
                "application__user__id",
                "application__user__email",
                "unit__pk",
                "score",
            )
        }
        return super().get_context_data(**ctx)


class SubmissionDownloadView(AdmissionsStaffViewMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            submission: Submission = Submission.objects.get(id=kwargs["pk"])
        except Submission.DoesNotExist:
            raise Http404

        return FileResponse(submission.notebook)


class SubmissionFeedbackDownloadView(AdmissionsStaffViewMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            submission: Submission = Submission.objects.get(id=kwargs["pk"])
        except Submission.DoesNotExist:
            raise Http404

        return FileResponse(submission.feedback)


class SelectionListView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/selections.html"

    def get_context_data(self, **kwargs):
        all_passed_test = SelectionQueries.filter_by_status_in(
            [SelectionStatus.PASSED_TEST]
        )
        all_drawn = SelectionQueries.filter_by_status_in(
            [SelectionStatus.DRAWN]
        )
        all_after_draw = SelectionQueries.filter_by_status_in(
            [
                SelectionStatus.INTERVIEW,
                SelectionStatus.SELECTED,
                SelectionStatus.TO_BE_ACCEPTED,
                SelectionStatus.ACCEPTED,
            ]
        )

        # no scholarships
        passed_test_no_scholarships = SelectionQueries.no_scholarships(
            all_passed_test
        )
        drawn_no_scholarships = SelectionQueries.no_scholarships(all_drawn)
        after_draw_no_scholarships = SelectionQueries.no_scholarships(
            all_after_draw
        )

        drawn_candidates_no_scholarships = drawn_no_scholarships.count()
        drawn_female_no_scholarships = drawn_no_scholarships.filter(
            user__gender="female"
        ).count()
        drawn_company_no_scholarships = drawn_no_scholarships.filter(
            user__ticket_type=TicketType.company
        ).count()

        selected_accepted_candidates_no_scholarships = (
            after_draw_no_scholarships.count()
        )
        selected_accepted_female_no_scholarships = (
            after_draw_no_scholarships.filter(
                user__gender=Gender.female
            ).count()
        )
        selected_accepted_company_no_scholarships = (
            after_draw_no_scholarships.filter(
                user__ticket_type=TicketType.company
            ).count()
        )

        left_out_candidates_no_scholarships = (
            passed_test_no_scholarships.count()
        )
        left_out_females_no_scholarships = passed_test_no_scholarships.filter(
            user__gender=Gender.female
        ).count()
        left_out_non_company_no_scholarships = (
            passed_test_no_scholarships.filter(
                user__ticket_type=TicketType.company
            ).count()
        )

        # scholarships
        passed_test_scholarships = SelectionQueries.scholarships(
            all_passed_test
        )
        drawn_scholarships = SelectionQueries.scholarships(all_drawn)
        after_draw_scholarships = SelectionQueries.scholarships(all_after_draw)

        drawn_candidates_scholarships = drawn_scholarships.count()
        drawn_female_scholarships = drawn_scholarships.filter(
            user__gender=Gender.female
        ).count()
        drawn_company_scholarships = drawn_scholarships.filter(
            user__ticket_type=TicketType.company
        ).count()

        selected_accepted_candidates_scholarships = (
            after_draw_scholarships.count()
        )
        selected_accepted_female_scholarships = after_draw_scholarships.filter(
            user__gender=Gender.female
        ).count()
        selected_accepted_company_scholarships = (
            after_draw_scholarships.filter(
                user__ticket_type=TicketType.company
            ).count()
        )

        left_out_candidates_scholarships = passed_test_scholarships.count()
        left_out_females_scholarships = passed_test_scholarships.filter(
            user__gender=Gender.female
        ).count()
        left_out_non_company_scholarships = passed_test_scholarships.filter(
            user__ticket_type=TicketType.company
        ).count()

        ctx = {
            "first_table_candidates": all_after_draw,
            "second_table_candidates": all_drawn,
            "summary": {
                "no_scholarship": {
                    "drawn_candidates": drawn_candidates_no_scholarships,
                    "drawn_female": drawn_female_no_scholarships,
                    "drawn_company": drawn_company_no_scholarships,
                    "selected_accepted_candidates": selected_accepted_candidates_no_scholarships,
                    "selected_accepted_female": selected_accepted_female_no_scholarships,
                    "selected_accepted_company": selected_accepted_company_no_scholarships,
                    "total_candidates": drawn_candidates_no_scholarships
                    + selected_accepted_candidates_no_scholarships,
                    "total_female": drawn_female_no_scholarships
                    + selected_accepted_female_no_scholarships,
                    "total_company": drawn_company_no_scholarships
                    + selected_accepted_company_no_scholarships,
                    "pct_candidates": (
                        drawn_candidates_no_scholarships
                        + selected_accepted_candidates_no_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "pct_female": (
                        drawn_female_no_scholarships
                        + selected_accepted_female_no_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "pct_company": (
                        drawn_company_no_scholarships
                        + selected_accepted_company_no_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "left_out_candidates": left_out_candidates_no_scholarships,
                    "left_out_females": left_out_females_no_scholarships,
                    "left_out_non_company": left_out_non_company_no_scholarships,
                },
                "scholarship": {
                    "drawn_candidates": drawn_candidates_scholarships,
                    "drawn_female": drawn_female_scholarships,
                    "drawn_company": drawn_company_scholarships,
                    "selected_accepted_candidates": selected_accepted_candidates_scholarships,
                    "selected_accepted_female": selected_accepted_female_scholarships,
                    "selected_accepted_company": selected_accepted_company_scholarships,
                    "total_candidates": drawn_candidates_scholarships
                    + selected_accepted_candidates_scholarships,
                    "total_female": drawn_female_scholarships
                    + selected_accepted_female_scholarships,
                    "total_company": drawn_company_scholarships
                    + selected_accepted_company_scholarships,
                    "pct_candidates": (
                        drawn_candidates_scholarships
                        + selected_accepted_candidates_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "pct_female": (
                        drawn_female_scholarships
                        + selected_accepted_female_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "pct_company": (
                        drawn_company_scholarships
                        + selected_accepted_company_scholarships
                    )
                    / default_draw_params.number_of_seats
                    * 100,
                    "left_out_candidates": left_out_candidates_scholarships,
                    "left_out_females": left_out_females_scholarships,
                    "left_out_non_company": left_out_non_company_scholarships,
                },
            },
        }
        return super().get_context_data(**ctx)


class SelectionDrawView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        draw(default_draw_params, scholarships=False)
        draw(default_draw_params, scholarships=True)
        return redirect("admissions:staff:selection-list")


class SelectionRejectView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        selection = Selection.objects.get(id=kwargs["candidate_id"])
        reject_draw(selection)
        return redirect("admissions:staff:selection-list")


class SelectionSelectView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        select()
        return redirect("admissions:staff:selection-list")


class InterviewListView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "./staff_templates/interviews.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "selections": SelectionQueries.filter_by_status_in(
                [SelectionStatus.INTERVIEW]
            ),
            "selection_status": SelectionStatus,
        }
        return super().get_context_data(**ctx)


def _get_user_selection(user_id):
    try:
        candidate = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404

    try:
        selection = Selection.objects.get(user=candidate)
    except User.DoesNotExist:
        raise Http404

    return candidate, selection


class InterviewDetailView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "./staff_templates/interview_id.html"

    def get_context_data(self, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])

        if SelectionDomain.get_status(selection) != SelectionStatus.INTERVIEW:
            return redirect("admissions:staff:interview-list")

        ctx = {
            "s": selection,
            "candidate_id": kwargs["pk"],
            "logs": get_selection_logs(selection),
        }
        return super().get_context_data(**ctx)

    def get(self, request, *args, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])
        if SelectionDomain.get_status(selection) != SelectionStatus.INTERVIEW:
            return redirect("admissions:staff:interview-list")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])
        staff_user = request.user
        action = request.POST["action"]
        msg = request.POST.get("msg", None)

        if action == "note":
            add_note(selection, msg, staff_user)
        elif action == "reject":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.REJECTED, staff_user, msg=msg
            )
            emails.send_interview_failed_email(
                to_email=selection.user.email,
                to_name=selection.user.name,
                message=msg,
            )
        elif action == "accept":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.SELECTED, staff_user, msg=msg
            )
            load_payment_data(selection)

            payment_due_date = selection.payment_due_date.strftime("%Y-%m-%d")
            emails.send_interview_passed_email(
                to_email=selection.user.email,
                to_name=selection.user.name,
                payment_value=selection.payment_value,
                payment_due_date=payment_due_date,
            )

        return redirect(request.path_info)  # TODO check get_success_url


class PaymentListView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/payments.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "selections": SelectionQueries.filter_by_status_in(
                [
                    SelectionStatus.SELECTED,
                    SelectionStatus.TO_BE_ACCEPTED,
                    SelectionStatus.ACCEPTED,
                    SelectionStatus.REJECTED,
                ]
            ),
            "selection_status": SelectionStatus,
        }
        return super().get_context_data(**ctx)


class PaymentDetailView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/payment_id.html"

    def get_context_data(self, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])
        ctx = {
            "s": selection,
            "selection_status": SelectionStatus,
            "can_update": can_be_updated(selection),
            "candidate_id": kwargs["pk"],
            "docs": [
                {
                    "url": reverse(
                        "admissions:candidate:payment-document-download",
                        args=(doc.pk,),
                    ),
                    "doc_type": doc.doc_type,
                    "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for doc in selection.documents.all().order_by("-created_at")
            ],
            "logs": get_selection_logs(selection),
        }
        return super().get_context_data(**ctx)

    def post(self, request, *args, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])
        staff_user = request.user
        action = request.POST["action"]
        msg = request.POST.get("msg", None)

        if action == "note":
            add_note(selection, msg, staff_user)
        elif action == "reject":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.REJECTED, staff_user, msg=msg
            )
            emails.send_payment_refused_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.name,
                message=msg,
            )
        elif action == "ask_additional":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.SELECTED, staff_user, msg=msg
            )
            emails.send_payment_need_additional_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.name,
                message=msg,
            )
        elif action == "accept":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.ACCEPTED, staff_user, msg=msg
            )
            emails.send_payment_accepted_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.name,
                message=msg,
            )

        return redirect(request.path_info)  # TODO check get_success_url


class PaymentResetView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        _, selection = _get_user_selection(kwargs["pk"])
        try:
            load_payment_data(selection, request.user)
            SelectionDomain.update_status(
                selection, SelectionStatus.SELECTED, user=request.user
            )
        except Exception:
            raise Http404

        return redirect("staff:payments", args=(kwargs["pk"],))


class ExportView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/exports.html"


class ExportCandidatesView(AdmissionsStaffViewMixin, View):
    template_name = "staff_templates/exports.html"

    def get(self, request, *args, **kwargs):
        export_data = get_all_candidates()
        filename = f"candidates@{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M')}.csv"

        response = HttpResponse(status=200, content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{filename}.csv"'

        w = csv.DictWriter(response, export_data.headers, lineterminator="\n")
        w.writeheader()
        w.writerows(export_data.rows)

        return response
