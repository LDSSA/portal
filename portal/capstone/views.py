import logging

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.users.views import StudentMixin, InstructorMixin
from portal.capstone import models, forms


logger = logging.getLogger(__name__)


class StudentCapstoneListView(StudentMixin, ListView):
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/student/capstone_list.html"

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        data = []
        for capstone in self.object_list:
            api, _ = models.StudentApi.objects.get_or_create(
                capstone=capstone, student=request.user
            )
            data.append((capstone, api))

        context = self.get_context_data(object_list=data)
        return self.render_to_response(context)


class StudentCapstoneDetailView(StudentMixin, DetailView):
    model = models.Capstone
    template_name = "capstone/student/capstone_detail.html"

    # noinspection PyAttributeOutsideInit
    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)

        api, _ = models.StudentApi.objects.get_or_create(
            capstone=self.object, student=self.request.user
        )

        return self.object, api

    def get(self, request, *args, **kwargs):
        capstone, api = self.get_object()
        context = self.get_context_data(
            capstone=capstone,
            api=api,
            api_form=forms.ApiForm(instance=api),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        capstone, api = self.get_object()

        api_form = forms.ApiForm(request.POST, instance=api)
        if api_form.is_valid():
            api_form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "capstone:student-capstone-detail", args=(self.object.pk,)
        )


class InstructorCapstoneListView(InstructorMixin, ListView):
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/instructor/capstone_list.html"


class InstructorCapstoneDetailView(InstructorMixin, DetailView):
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/instructor/capstone_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(
            object=self.object,
            student_apis=self.object.studentapi_set.all(),
        )
        return self.render_to_response(context)


class CapstonePredictView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return Response({"proba": 0.6})


class CapstoneUpdateView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return Response({"msg": "ok"})
