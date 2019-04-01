from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from portal.academy import models


class UnitDetailView(LoginRequiredMixin, DetailView):
    model = models.Unit


class UnitListView(LoginRequiredMixin, ListView):

    model = models.Unit
    queryset = models.Unit.objects.order_by('due_date')
    slug_field = "unit"
    slug_url_kwarg = "unit"


class UnitUpdateView(LoginRequiredMixin, UpdateView):

    model = models.Unit
    fields = ["code"]

