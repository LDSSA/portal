from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, UpdateView
from rest_framework import generics
from rest_framework.settings import import_from_string

from portal.academy import models, serializers, services


class UnitListView(LoginRequiredMixin, ListView):

    model = models.Unit
    queryset = models.Unit.objects.order_by('due_date')
    slug_field = "unit"
    slug_url_kwarg = "unit"

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        data = []
        for unit in self.object_list:
            grade, _ = models.Grade.objects.get_or_create(
                student=request.user,
                unit=unit)
            data.append((unit, grade))

        context = self.get_context_data(object_list=data)
        return self.render_to_response(context)


class UnitDetailView(LoginRequiredMixin, DetailView):
    model = models.Unit

    def get(self, request, *args, **kwargs):
        unit, grade = self.get_object()
        context = self.get_context_data(unit=unit, grade=grade)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)
        unit = self.object

        grade, _ = models.Grade.objects.get_or_create(
            student=self.request.user,
            unit=self.kwargs.get('pk'))

        return unit, grade

    def post(self, request, *args, **kwargs):
        unit, grade = self.get_object()

        if not unit.checksum:
            raise RuntimeError("Not checksum present for this unit")

        grading_fcn = import_from_string(settings.GRADING_FCN, 'GRADING_FCN')
        grading_fcn(request.user, unit)
        return self.get(request, *args, **kwargs)


class UnitUpdateView(LoginRequiredMixin, UpdateView):

    model = models.Unit
    fields = ["code"]


class GradingView(generics.RetrieveUpdateAPIView):
    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer

    def get_object(self):
        user = get_user_model().objects.get(
            username=self.kwargs.get('username'))
        unit = models.Unit.objects.get(code=self.kwargs.get('unit'))
        grade, _ = models.Grade.objects.get_or_create(
            student=user,
            unit=unit)

        # May raise a permission denied
        self.check_object_permissions(self.request, grade)

        return grade


class ChecksumView(generics.RetrieveUpdateAPIView):
    queryset = models.Unit.objects.all()
    serializer_class = serializers.ChecksumSerializer

