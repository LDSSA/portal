import logging

from django.utils import timezone
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from . import forms
from portal.admissions import domain

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRequiredFieldsMixin:
    required_fields = (
        "name",
        "slack_member_id",
        "github_username",
    )

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if any(
                getattr(request.user, field) == ""
                for field in self.required_fields
            ):
                return redirect("users:profile")

        return super().dispatch(request, *args, **kwargs)


class AdmissionsOngoingMixin:
    """Verify that the current user is authenticated."""
    def dispatch(self, request, *args, **kwargs):
        if domain.admissions_open():
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class AdmissionsEndedMixin:
    """Verify that the current user is authenticated."""
    def dispatch(self, request, *args, **kwargs):
        if domain.admissions_ended():
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class InstructorMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_instructor or request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission()


class InstructorViewsMixin(LoginRequiredMixin, UserRequiredFieldsMixin, AdmissionsEndedMixin, InstructorMixin):
    pass


class StudentMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_student:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class StudentViewsMixin(LoginRequiredMixin, UserRequiredFieldsMixin, AdmissionsOngoingMixin, StudentMixin):
    pass


class AdmissionsStaffMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsStaffViewMixin(LoginRequiredMixin, UserRequiredFieldsMixin, AdmissionsOngoingMixin, AdmissionsStaffMixin):
    pass


class AdmissionsCandidateMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsCandidateViewMixin(
    LoginRequiredMixin, UserRequiredFieldsMixin, AdmissionsOngoingMixin,
):
    pass


class CandidateAcceptedCoCMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.code_of_conduct_accepted:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)



# TODO TODO
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
