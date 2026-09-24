import logging

from allauth.account.views import SignupView
from constance import config
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    AccessMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from portal.admissions.policy import academy_open, email_verified, registration_ready
from portal.selection.enrollment import complete_registration

from . import forms

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRequiredFieldsMixin:
    required_academy_fields = (
        "name",
        "slack_member_id",
        "github_username",
    )
    required_admissions_fields = (
        "name",
        "gender",
        "ticket_type",
    )

    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if request.user.is_authenticated:
            if request.user.is_staff:
                required_fields = []
            elif request.user.is_student or request.user.is_instructor:
                required_fields = self.required_academy_fields
            else:
                required_fields = self.required_admissions_fields
            missing_fields = [
                field for field in required_fields if getattr(request.user, field) == ""
            ]
            if missing_fields:
                logger.info("Missing fields %s", missing_fields)
                return redirect("users:profile")

        return super().dispatch(request, *args, **kwargs)


class AdmissionsOngoingMixin:
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if config.PORTAL_STATUS.startswith("admissions"):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class InstructorMixin:
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if (
            request.user.is_instructor
            or request.user.is_superuser
            or request.user.is_staff
        ):
            return super().dispatch(request, *args, **kwargs)

        return self.handle_no_permission()


class InstructorViewsMixin(
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    InstructorMixin,
):
    pass


class StudentMixin(AccessMixin):
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_student or (
            not request.user.admissions_requires_exam and not academy_open(request.user)
        ):
            return self.handle_no_permission()
        if getattr(self, "requires_course_progression", True):
            from portal.academy.services import progression_block_reason

            reason = progression_block_reason(request.user)
            if reason:
                messages.warning(request, reason)
                return redirect("academy:student-unit-list")
        return super().dispatch(request, *args, **kwargs)


class StudentViewsMixin(
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    StudentMixin,
):
    pass


class AdmissionsStaffMixin:
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsStaffViewMixin(
    LoginRequiredMixin,
    AdmissionsStaffMixin,
):
    pass


class AdmissionsCandidateMixin:
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.is_instructor
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsViewMixin(
    LoginRequiredMixin,
):
    pass


class VerifiedEmailMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not email_verified(request.user):
            return redirect("account_email_verification_sent")
        return super().dispatch(request, *args, **kwargs)


class ExamCandidateRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            if not request.user.admissions_requires_exam:
                raise Http404
            if not config.PORTAL_STATUS.startswith("admissions"):
                raise Http404
            if not registration_ready(request.user):
                return redirect("admissions:candidate:home")
        return super().dispatch(request, *args, **kwargs)


class AdmissionsCandidateViewMixin(
    LoginRequiredMixin,
    VerifiedEmailMixin,
    AdmissionsCandidateMixin,
):
    pass


class CandidateAcceptedCoCMixin:
    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):
        if request.user.is_authenticated and not request.user.code_of_conduct_accepted:
            return redirect("admissions:candidate:codeofconduct")
        return super().dispatch(request, *args, **kwargs)


class CandidateScholarshipDecidedMixin(AdmissionsCandidateMixin, UserPassesTestMixin):
    """Verify that the current user is an instructor."""

    def test_func(self):
        if not self.request.user.is_staff:
            return False
        return True


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserListView(LoginRequiredMixin, ListView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_list_view = UserListView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.UserChangeForm
    template_name = "users/user_form.html"  # Explicitly specify the template name

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse("users:profile")

    def form_valid(self, form):
        # Rebuild on a locked instance so a concurrent scholarship/payment decision
        # cannot be undone by saving a stale profile form.
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=self.request.user.pk)
            locked_form = self.form_class(self.request.POST, instance=user)
            if not locked_form.is_valid():
                return self.form_invalid(locked_form)
            try:
                with transaction.atomic():
                    self.object = locked_form.save()
                    complete_registration(self.object)
            except ValidationError as exc:
                locked_form.add_error(None, exc)
                return self.form_invalid(locked_form)
        messages.success(self.request, "Your profile was updated successfully.")
        return redirect(self.get_success_url())


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        # return reverse("users:detail", kwargs={"username": self.request.user.username})
        return reverse("users:profile")


user_redirect_view = UserRedirectView.as_view()


class InstructorsSignupView(SignupView):
    template_name = "users/instructors_signup.html"
