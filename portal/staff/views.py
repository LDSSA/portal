from datetime import datetime
from logging import getLogger
from typing import Any, Dict

from constance import config
from django.http import (
    HttpResponseServerError,
    Http404,
)
from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from portal.users.views import AdmissionsStaffViewMixin
from portal.users.models import User
from portal.staff.domain import Events, EventsException
from portal.applications.models import Submission, SubmissionTypes, Application
from portal.applications.domain import Domain as ApplicationDomain, Status
from portal.selection.draw import default_draw_params, draw, reject_draw
from portal.selection.models import Selection
from portal.selection.queries import SelectionQueries
from portal.selection.select import select
from portal.selection.status import SelectionStatus
from portal.selection.domain import SelectionDomain
from portal.selection.logs import get_selection_logs
from portal.selection.payment import (
    add_note,
    load_payment_data,
    can_be_updated,
)

logger = getLogger(__name__)


DATETIME_FMT = "%d/%m/%Y %H:%M:%S"


class HomeView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/home.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "user": self.request.user,
            "datetime_fmt": DATETIME_FMT,
            "datetime_flags": [
                {
                    "key": "applications_opening_date",
                    "value": config.ADMISSIONS_APPLICATIONS_OPENING_DATE.strftime(
                        DATETIME_FMT
                    ),
                    "label": "Challenge Submissions Opening Date",
                },
                {
                    "key": "applications_closing_date",
                    "value": config.ADMISSIONS_APPLICATIONS_CLOSING_DATE.strftime(
                        DATETIME_FMT
                    ),
                    "label": "Challenge Submissions Closing Date",
                },
            ],
            "int_flags": [
                {
                    "key": "coding_test_duration",
                    "value": config.ADMISSIONS_CODING_TEST_DURATION,
                    "label": "Coding Test Duration in minutes",
                }
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
        if not request.user.is_admin:
            return HttpResponseServerError(
                b"error updating admin variables. Only admins can update these variables"
            )

        key = request.POST["key"]

        if key == "applications_opening_date":
            date_s = request.POST["date_s"]
            if not interface.feature_flag_client.set_applications_opening_date(
                datetime.strptime(date_s, DATETIME_FMT)
            ):
                return HttpResponseServerError(
                    b"error setting opening date. opening date must be before closing date"
                )

        elif key == "applications_closing_date":
            date_s = request.POST["date_s"]
            if not interface.feature_flag_client.set_applications_closing_date(
                datetime.strptime(date_s, DATETIME_FMT)
            ):
                return HttpResponseServerError(
                    b"error setting closing date. closing date must be after opening date"
                )

        elif key == "coding_test_duration":
            interface.feature_flag_client.set_coding_test_duration(
                int(request.POST["int_s"])
            )

        elif key == "signups_are_open":
            if request.POST["action"] == "open":
                interface.feature_flag_client.open_signups()
            else:
                interface.feature_flag_client.close_signups()

        elif key == "accepting_payment_profs":
            if request.POST["action"] == "open":
                interface.feature_flag_client.open_payment_profs()
            else:
                interface.feature_flag_client.close_payment_profs()
        else:
            logger.warning(f"unknown feature flag key `{key}`.. doing nothing")

        return redirect("staff:home")


class EventsView(AdmissionsStaffViewMixin, TemplateView):
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
        if not request.user.is_admin:
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

        return redirect("staff:events")


class CandidateListView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/candidates.html"

    def get_context_data(self, **kwargs):
        ctx = {
            "users": User.objects.filter(is_staff=False)
            .filter(is_admin=False)
            .order_by("email")
        }
        return super().get_context_data(**ctx)


class CandidateDetailView(AdmissionsStaffViewMixin, TemplateView):
    template_name = "staff_templates/candidate.html"

    def get_context_data(self, **kwargs):
        try:
            user = (
                User.objects.filter(is_staff=False)
                .filter(is_admin=False)
                .get(id=user_id)
            )
        except User.DoesNotExist:
            raise Http404

        try:
            application = user.application
            total_submissions = Submission.objects.filter(
                application=application
            ).count()
            application_best_scores = {
                SubmissionTypes.coding_test.uname: ApplicationDomain.get_best_score(
                    application, SubmissionTypes.coding_test
                ),
                SubmissionTypes.slu01.uname: ApplicationDomain.get_best_score(
                    application, SubmissionTypes.slu01
                ),
                SubmissionTypes.slu02.uname: ApplicationDomain.get_best_score(
                    application, SubmissionTypes.slu02
                ),
                SubmissionTypes.slu03.uname: ApplicationDomain.get_best_score(
                    application, SubmissionTypes.slu03
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
            SubmissionTypes.coding_test.uname: {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            SubmissionTypes.slu01.uname: {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            SubmissionTypes.slu02.uname: {
                s: 0
                for s in [
                    Status.not_started.name,
                    Status.ongoing.name,
                    Status.passed.name,
                    Status.failed.name,
                ]
            },
            SubmissionTypes.slu03.uname: {
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
            application_det_status = ApplicationDomain.get_application_detailed_status(a)
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
                            ApplicationDomain.get_sub_type_status(a, sub_type)
                            for sub_type in SubmissionTypes.all
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
                "submission_type",
                "score",
            )
        }
        return super().get_context_data(**ctx)


class SubmissionDownloadView(AdmissionsStaffViewMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            submission: Submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            raise Http404

        url = interface.storage_client.get_attachment_url(
            submission.file_location,
            content_type="application/vnd.jupyter",
            filename=f"{submission.id}.ipynb",
        )

        return redirect(url)


class SubmissionFeedbackDownloadView(AdmissionsStaffViewMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            submission: Submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            raise Http404
        url = interface.storage_client.get_url(
            submission.feedback_location, content_type="text/html"
        )

        return redirect(url)


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
            user__profile__gender='female'
        ).count()
        drawn_company_no_scholarships = drawn_no_scholarships.filter(
            user__profile__ticket_type=ProfileTicketTypes.company
        ).count()

        selected_accepted_candidates_no_scholarships = (
            after_draw_no_scholarships.count()
        )
        selected_accepted_female_no_scholarships = (
            after_draw_no_scholarships.filter(
                user__profile__gender=ProfileGenders.female
            ).count()
        )
        selected_accepted_company_no_scholarships = (
            after_draw_no_scholarships.filter(
                user__profile__ticket_type=ProfileTicketTypes.company
            ).count()
        )

        left_out_candidates_no_scholarships = (
            passed_test_no_scholarships.count()
        )
        left_out_females_no_scholarships = passed_test_no_scholarships.filter(
            user__profile__gender=ProfileGenders.female
        ).count()
        left_out_non_company_no_scholarships = (
            passed_test_no_scholarships.filter(
                user__profile__ticket_type=ProfileTicketTypes.company
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
            user__profile__gender=ProfileGenders.female
        ).count()
        drawn_company_scholarships = drawn_scholarships.filter(
            user__profile__ticket_type=ProfileTicketTypes.company
        ).count()

        selected_accepted_candidates_scholarships = (
            after_draw_scholarships.count()
        )
        selected_accepted_female_scholarships = after_draw_scholarships.filter(
            user__profile__gender=ProfileGenders.female
        ).count()
        selected_accepted_company_scholarships = (
            after_draw_scholarships.filter(
                user__profile__ticket_type=ProfileTicketTypes.company
            ).count()
        )

        left_out_candidates_scholarships = passed_test_scholarships.count()
        left_out_females_scholarships = passed_test_scholarships.filter(
            user__profile__gender=ProfileGenders.female
        ).count()
        left_out_non_company_scholarships = passed_test_scholarships.filter(
            user__profile__ticket_type=ProfileTicketTypes.company
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
        return redirect("staff:selections")


class SelectionRejectView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        selection = Selection.objects.get(id=candidate_id)
        reject_draw(selection)
        return redirect("staff:selections")


class SelectionSelectView(AdmissionsStaffViewMixin, View):
    def post(self, request, *args, **kwargs):
        select()
        return redirect("staff:selections")


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


# TODO TODO deal with 404
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
    template_name = "./staff_templates/interviews.html"

    def get_context_data(self, **kwargs):
        _, selection = _get_user_selection(user_id)  # TODO user_id from url

        # TODO TODO move to correct place
        if SelectionDomain.get_status(selection) != SelectionStatus.INTERVIEW:
            return redirect("staff:interviews")

        ctx = {
            "s": selection,
            "candidate_id": candidate_id,
            "logs": get_selection_logs(selection),
        }
        return super().get_context_data(**ctx)

    def post(self, request, user_id):
        _, selection = _get_user_selection(user_id)
        staff_user = request.user
        action = request.POST["action"]
        msg = request.POST.get("msg", None)

        if action == "note":
            add_note(selection, msg, staff_user)
        elif action == "reject":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.REJECTED, staff_user, msg=msg
            )
            interface.email_client.send_interview_failed_email(
                to_email=selection.user.email,
                to_name=selection.user.profile.name,
                message=msg,
            )
        elif action == "accept":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.SELECTED, staff_user, msg=msg
            )
            load_payment_data(selection)

            payment_due_date = selection.payment_due_date.strftime("%Y-%m-%d")
            interface.email_client.send_interview_passed_email(
                to_email=selection.user.email,
                to_name=selection.user.profile.name,
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
        _, selection = _get_user_selection(user_id)  # TODO TODO TODO
        ctx = {
            "s": selection,
            "selection_status": SelectionStatus,
            "can_update": can_be_updated(selection),
            "candidate_id": candidate_id,  # TODO
            "docs": [
                {
                    "url": interface.storage_client.get_url(
                        doc.file_location, content_type="image"
                    ),
                    "doc_type": doc.doc_type,
                    "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for doc in selection.documents.all().order_by("-created_at")
            ],
            "logs": get_selection_logs(selection),
        }
        return super().get_context_data(**ctx)

    def post(self, request, user_id):
        _, selection = _get_user_selection(user_id)
        staff_user = request.user
        action = request.POST["action"]
        msg = request.POST.get("msg", None)

        if action == "note":
            add_note(selection, msg, staff_user)
        elif action == "reject":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.REJECTED, staff_user, msg=msg
            )
            interface.email_client.send_payment_refused_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.profile.name,
                message=msg,
            )
        elif action == "ask_additional":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.SELECTED, staff_user, msg=msg
            )
            interface.email_client.send_payment_need_additional_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.profile.name,
                message=msg,
            )
        elif action == "accept":
            SelectionDomain.manual_update_status(
                selection, SelectionStatus.ACCEPTED, staff_user, msg=msg
            )
            interface.email_client.send_payment_accepted_proof_email(
                to_email=selection.user.email,
                to_name=selection.user.profile.name,
                message=msg,
            )

        return redirect(request.path_info)  # TODO check get_success_url


class PaymentResetView(AdmissionsStaffViewMixin, View):
    def post(self, request, user_id):
        _, selection = _get_user_selection(user_id)
        try:
            load_payment_data(selection, request.user)
            SelectionDomain.update_status(
                selection, SelectionStatus.SELECTED, user=request.user
            )
        except Exception:
            raise Http404

        return redirect("staff:payments", args=(user_id,))


# class PaymentDetailView(AdmissionsStaffViewMixin, TemplateView):
#     template_name = "staff_templates/exports.html"


# class PaymentDetailView(AdmissionsStaffViewMixin, View):
#     template_name = "staff_templates/exports.html"

#     def get(self, **kwargs):
#         export_data = get_all_candidates()
#         filename = (
#             f"candidates@{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H:%M')}.csv"
#         )

#         response = HttpResponse(status=200, content_type="text/csv")
#         response[
#             "Content-Disposition"
#         ] = f'attachment; filename="{filename}.csv"'

#         w = csv.DictWriter(response, export_data.headers, lineterminator="\n")
#         w.writeheader()
#         w.writerows(export_data.rows)

#         return response
