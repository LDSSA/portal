from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from . import forms

User = get_user_model()


class UserRequiredFieldsMixin:
    required_fields = (
        'name',
        'slack_member_id',
        'github_username',
    )
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if any(getattr(request.user, field) == ''
                   for field in self.required_fields):
                return redirect('users:profile')

        return super().dispatch(request, *args, **kwargs)

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
