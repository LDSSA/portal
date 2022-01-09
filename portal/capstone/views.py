import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.capstone import models, forms
from portal.users.models import User
from portal.users.views import StudentMixin, InstructorMixin


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
                capstone=capstone, user=request.user
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
            capstone=self.object, user=self.request.user
        )

        report = None
        current_report = self.object.get_current_due_report()
        if current_report:
            report, _ = models.Report.objects.get_or_create(
                capstone=self.object,
                user=self.request.user,
                type=current_report)

        return self.object, api, report

    def get(self, request, *args, **kwargs):
        capstone, api, report = self.get_object()
        context = self.get_context_data(
            capstone=capstone,
            api=api,
            api_form=forms.ApiForm(instance=api),
            report=report,
            report_form=forms.ReportForm(instance=report),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        capstone, api, report = self.get_object()

        if "submit_api" in request.POST:
            form = forms.ApiForm(request.POST, instance=api)
            if form.is_valid():
                form.save()

        elif "submit_report" in request.POST:
            current_report = capstone.get_current_due_report
            if current_report is None:
                raise forms.ValidationError("Not accepting reports at the moment!")

            form = forms.ReportForm(request.POST, request.FILES, instance=report)
            if form.is_valid():
                form.save()
                messages.add_message(
                    request, messages.SUCCESS, "Report submited successfully!"
                )

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
        student_data = []
        for student in User.objects.filter(is_student=True):
            student_data.append({
                'user': student,
                'api': models.StudentApi.objects.filter(capstone=self.object, user=student).first(),
                'report_1_provisory': models.Report.objects.filter(capstone=self.object, user=student, type=models.Report.Type.report_1_provisory).first(),
                'report_1_final': models.Report.objects.filter(capstone=self.object, user=student, type=models.Report.Type.report_1_final).first(),
                'report_2_provisory': models.Report.objects.filter(capstone=self.object, user=student, type=models.Report.Type.report_2_provisory).first(),
                'report_2_final': models.Report.objects.filter(capstone=self.object, user=student, type=models.Report.Type.report_2_final).first(),
            })

        context = self.get_context_data(
            object=self.object,
            students=student_data,
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
