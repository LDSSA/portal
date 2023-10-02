import logging  # noqa: D100

from allauth.account.views import SignupView
from constance import config
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from . import forms

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRequiredFieldsMixin:  # noqa: D101
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

    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if request.user.is_authenticated:
            if config.PORTAL_STATUS.startswith("admissions"):
                if request.user.is_staff:
                    required_fields = []
                else:
                    required_fields = self.required_admissions_fields
            elif config.PORTAL_STATUS.startswith("academy"):
                required_fields = self.required_academy_fields
            missing_fields = [
                field for field in required_fields if getattr(request.user, field) == ""
            ]
            if missing_fields:
                logger.info("Missing fields %s", missing_fields)
                return redirect("users:profile")

        return super().dispatch(request, *args, **kwargs)


class AdmissionsOngoingMixin:  # noqa: D101
    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if config.PORTAL_STATUS.startswith("admissions"):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class InstructorMixin:  # noqa: D101
    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_instructor or request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        return self.handle_no_permission()


class InstructorViewsMixin(  # noqa: D101
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    InstructorMixin,
):
    pass


class StudentMixin:  # noqa: D101
    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_student:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class StudentViewsMixin(  # noqa: D101
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    StudentMixin,
):
    pass


class AdmissionsStaffMixin:  # noqa: D101
    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsStaffViewMixin(  # noqa: D101
    LoginRequiredMixin,
    UserRequiredFieldsMixin,
    AdmissionsOngoingMixin,
    AdmissionsStaffMixin,
):
    pass


class AdmissionsCandidateMixin:  # noqa: D101
    def dispatch(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        if request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdmissionsViewMixin(  # noqa: D101
    LoginRequiredMixin,
    AdmissionsOngoingMixin,
):
    pass


class AdmissionsCandidateViewMixin(  # noqa: D101
    LoginRequiredMixin,
    AdmissionsOngoingMixin,
    AdmissionsCandidateMixin,
):
    pass


class CandidateAcceptedCoCMixin:  # noqa: D101
    def dispatch(  # noqa: ANN101, ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):
        if not request.user.code_of_conduct_accepted:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CandidateScholarshipDecidedMixin(AdmissionsCandidateMixin, UserPassesTestMixin):

    """Verify that the current user is an instructor."""  # noqa: D211

    def test_func(self):  # noqa: ANN101, ANN201, D102
        if not self.request.user.is_staff:
            return False
        return True


class UserDetailView(LoginRequiredMixin, DetailView):  # noqa: D101
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserListView(LoginRequiredMixin, ListView):  # noqa: D101
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_list_view = UserListView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):  # noqa: D101
    model = User
    form_class = forms.UserChangeForm

    def get_success_url(self) -> str:  # noqa: ANN101, D102
        return reverse("users:profile")

    def get_object(self):  # noqa: ANN101, ANN201, D102
        return User.objects.get(username=self.request.user.username)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):  # noqa: D101
    permanent = False

    def get_redirect_url(self):  # noqa: ANN101, ANN201, D102
        # return reverse("users:detail", kwargs={"username": self.request.user.username})  # noqa: ERA001
        return reverse("users:profile")


user_redirect_view = UserRedirectView.as_view()


class InstructorsSignupView(SignupView):  # noqa: D101
    template_name = "users/instructors_signup.html"
