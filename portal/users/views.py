import logging

from constance import config
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

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

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if config.PORTAL_STATUS.startswith("admissions"):
                if request.user.is_staff:
                    required_fields = []
                else:
                    required_fields = self.required_admissions_fields
            elif config.PORTAL_STATUS.startswith("academy"):
                required_fields = self.required_academy_fields
            missing_fields = [
                field
                for field in required_fields
                if getattr(request.user, field) == ""
            ]
            if missing_fields:
                logger.info("Missing fields %s", missing_fields)
                return redirect("users:profile")

        return super().dispatch(request, *args, **kwargs)


class AdmissionsOngoingMixin:
    def dispatch(self, request, *args, **kwargs):
        if config.PORTAL_STATUS.startswith("admissions"):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class InstructorMixin:
    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_instructor
            or request.user.is_superuser
            or request.user.is_staff
        ):
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission()


class InstructorViewsMixin(
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    InstructorMixin,
):
    pass


class StudentMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_student:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class StudentViewsMixin(
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    StudentMixin,
):
    pass


class AdmissionsStaffMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsStaffViewMixin(
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    AdmissionsOngoingMixin,
    AdmissionsStaffMixin,
):
    pass


class AdmissionsCandidateMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsViewMixin(
    LoginRequiredMixin,
    AdmissionsOngoingMixin,
):
    pass


class AdmissionsCandidateViewMixin(
    LoginRequiredMixin,
    AdmissionsOngoingMixin,
    AdmissionsCandidateMixin,
):
    pass


class CandidateAcceptedCoCMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.code_of_conduct_accepted:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CandidateScholarshipDecidedMixin(
    AdmissionsCandidateMixin, UserPassesTestMixin
):
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

    def get_success_url(self):
        return reverse("users:profile")

    def get_object(self):
        return User.objects.get(username=self.request.user.username)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        # return reverse("users:detail", kwargs={"username": self.request.user.username})
        return reverse("users:profile")


user_redirect_view = UserRedirectView.as_view()
