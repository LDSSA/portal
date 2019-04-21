from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, UpdateView
from rest_framework import viewsets
from rest_framework import  mixins

from portal.academy import models, serializers


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


class GradingViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer


class ChecksumViewSet(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Unit.objects.all()
    serializer_class = serializers.ChecksumSerializer
