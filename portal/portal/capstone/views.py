import logging  # noqa: D100

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.capstone import forms, models
from portal.users.models import User
from portal.users.views import InstructorMixin, StudentMixin

logger = logging.getLogger(__name__)


class StudentCapstoneListView(StudentMixin, ListView):  # noqa: D101
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/student/capstone_list.html"

    def get(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        self.object_list = self.get_queryset()
        data = []
        for capstone in self.object_list:
            api, _ = models.StudentApi.objects.get_or_create(capstone=capstone, user=request.user)
            data.append((capstone, api))

        context = self.get_context_data(object_list=data)
        return self.render_to_response(context)


class StudentCapstoneDetailView(StudentMixin, DetailView):  # noqa: D101
    model = models.Capstone
    template_name = "capstone/student/capstone_detail.html"

    # noinspection PyAttributeOutsideInit
    def get_object(self, queryset=None):  # noqa: ANN001, ANN101, ANN201, D102
        self.object = super().get_object(queryset=queryset)

        api, _ = models.StudentApi.objects.get_or_create(
            capstone=self.object,
            user=self.request.user,
        )

        reports = {}
        for type_choice in models.Report.Type.choices:
            report, _ = models.Report.objects.get_or_create(
                capstone=self.object,
                user=self.request.user,
                type=type_choice[0],
            )
            reports[type_choice[0]] = report

        return self.object, api, reports

    def get(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        capstone, api, reports = self.get_object()
        context = self.get_context_data(
            capstone=capstone,
            api=api,
            api_form=forms.ApiForm(instance=api),
            reports=[
                [report_type, forms.ReportForm(instance=report), report]
                for report_type, report in reports.items()
                if getattr(capstone, f"{report_type}_open")
            ],
        )
        return self.render_to_response(context)

    def post(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        capstone, api, reports = self.get_object()

        if "submit_api" in request.POST:
            form = forms.ApiForm(request.POST, instance=api)
            if form.is_valid():
                form.save()

        else:
            for report_type, report in reports.items():
                if f"submit_{report_type}" in request.POST:
                    form = forms.ReportForm(request.POST, request.FILES, instance=report)
                    if form.is_valid():
                        form.save()
                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            "Report submited successfully!",
                        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):  # noqa: ANN101, ANN201, D102
        return reverse("capstone:student-capstone-detail", args=(self.object.pk,))


class InstructorCapstoneListView(InstructorMixin, ListView):  # noqa: D101
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/instructor/capstone_list.html"


class InstructorCapstoneDetailView(InstructorMixin, DetailView):  # noqa: D101
    model = models.Capstone
    queryset = models.Capstone.objects.all()
    template_name = "capstone/instructor/capstone_detail.html"

    def get(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        self.object = self.get_object()
        student_data = []
        for student in User.objects.filter(is_student=True):
            student_data.append(  # noqa: PERF401
                {
                    "user": student,
                    "api": models.StudentApi.objects.filter(
                        capstone=self.object,
                        user=student,
                    ).first(),
                    "proposal": models.Report.objects.filter(
                        capstone=self.object,
                        user=student,
                        type=models.Report.Type.proposal,
                    ).first(),
                    "report_provisory": models.Report.objects.filter(
                        capstone=self.object,
                        user=student,
                        type=models.Report.Type.report_provisory,
                    ).first(),
                    "report_final": models.Report.objects.filter(
                        capstone=self.object,
                        user=student,
                        type=models.Report.Type.report_final,
                    ).first(),
                },
            )

        context = self.get_context_data(
            object=self.object,
            students=student_data,
            workspace_url=settings.SLACK_WORKSPACE,
        )
        return self.render_to_response(context)


class CapstonePredictView(APIView):  # noqa: D101
    permission_classes = []  # noqa: RUF012

    def post(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        return Response({"proba": 0.6})


class CapstoneUpdateView(APIView):  # noqa: D101
    permission_classes = []  # noqa: RUF012

    def post(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        return Response({"msg": "ok"})
