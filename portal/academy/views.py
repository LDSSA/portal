import logging

from constance import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, RedirectView
from rest_framework.settings import import_string

from portal.academy import models, serializers
from portal.users.views import StudentViewsMixin, InstructorViewsMixin


logger = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
class HomeRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if config.PORTAL_STATUS == "academy":
            if self.request.user.is_student:
                self.pattern_name = "academy:student-unit-list"
            elif (
                self.request.user.is_instructor
                or self.request.user.is_superuser
                or self.request.user.is_staff
            ):
                self.pattern_name = "academy:instructor-user-list"
            else:
                self.handle_no_permission()
        else:
            if self.request.user.is_staff:
                self.pattern_name = "admissions:staff:home"
            else:
                self.pattern_name = "admissions:candidate:home"

        return super().get_redirect_url(*args, **kwargs)


def get_grade(unit, user):
    grade = unit.grades.filter(user=user).order_by("-created").first()
    if grade is None:
        grade = models.Grade(user=user, unit=unit)
    return grade


class BaseUnitListView(ListView):
    model = models.Unit
    queryset = models.Unit.objects.order_by("-specialization", "-code")
    template_name = None
    detail_view_name = None

    # noinspection PyAttributeOutsideInit
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        data = []
        for unit in self.object_list:
            grade = get_grade(unit, request.user)
            data.append((unit, grade))

        context = self.get_context_data(
            object_list=data, detail_view_name=self.detail_view_name
        )
        return self.render_to_response(context)


class BaseUnitDetailView(DetailView):
    model = models.Unit
    template_name = None

    def get(self, request, *args, **kwargs):
        unit, grade = self.get_object()
        context = self.get_context_data(unit=unit, grade=grade)
        return self.render_to_response(context)

    # noinspection PyAttributeOutsideInit
    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)
        unit = self.object
        grade = (
            unit.grades.filter(user=self.request.user)
            .order_by("-created")
            .first()
        )
        if grade is None:
            grade = models.Grade(user=self.request.user, unit=unit)
        return unit, grade

    def post(self, request, *args, **kwargs):
        unit, _ = self.get_object()
        grade = models.Grade(user=self.request.user, unit=unit)

        if not unit.checksum:
            raise RuntimeError("Not checksum present for this unit")

        # Clear grade
        grade.status = "sent"
        grade.score = None
        grade.notebook = None
        grade.message = ""
        grade.save()

        # Send to grading
        Grading = import_string(settings.GRADING_CLASS)
        Grading(grade=grade).run_grading()

        return HttpResponseRedirect(request.path_info)


class StudentUnitListView(StudentViewsMixin, BaseUnitListView):
    template_name = "academy/student/unit_list.html"
    detail_view_name = "academy:student-unit-detail"


class StudentUnitDetailView(StudentViewsMixin, BaseUnitDetailView):
    template_name = "academy/student/unit_detail.html"


class InstructorUserListView(InstructorViewsMixin, ListView):
    model = get_user_model()
    queryset = get_user_model().objects.filter(is_student=True)
    template_name = "academy/instructor/user_list.html"

    def get_queryset(self):
        user_id = self.request.GET.get("user_id")
        if user_id:
            return self.queryset.filter(id=user_id)
        return self.queryset.all()

    # noinspection PyAttributeOutsideInit
    def get(self, request, *args, **kwargs):
        # Validate query params
        validator = serializers.InstructorsViewFiltersSerializer(
            data=self.request.GET
        )
        if not validator.is_valid():
            msg = " ".join(
                [
                    f"Filter '{k}': {v[0].lower()}"
                    for k, v in validator.errors.items()
                ]
            )
            messages.error(request, _(msg))
            return redirect("academy:instructor-user-list")
        query_params = validator.validated_data

        self.object_list = self.get_queryset()
        specializations = models.Specialization.objects

        grade_status = query_params.get("grade_status")
        score__gte = query_params.get("score__gte")
        score__lte = query_params.get("score__lte")
        unit_code = query_params.get("unit_code")
        spc_code = query_params.get("spc_code")
        if spc_code:
            specializations = specializations.filter(code=spc_code)

        specializations = specializations.order_by("code")
        spc_list = []
        unit_list = []
        max_score = 0
        for spc in specializations:
            qs = models.Unit.objects.filter(specialization=spc)
            if unit_code:
                qs = qs.filter(code=unit_code)
            qs = qs.order_by("due_date")
            max_score += qs.count() * 20
            spc.unit_count = qs.count()
            spc_list.append(spc)
            if qs.exists():
                unit_list += list(qs)
            else:
                unit_list += [None]

        object_list = []
        for user in self.object_list:
            total_score = 0
            user_data = {"user": user, "grades": [], "total_score": 0}
            for unit in unit_list:
                if unit is None:
                    user_data["grades"].append(None)

                else:
                    grade = get_grade(unit, user)
                    if grade_status and grade.status != grade_status:
                        user_data["grades"].append(None)
                        continue
                    if grade.status == "graded":
                        total_score += grade.score
                    user_data["grades"].append(grade)
            if score__gte and total_score < score__gte:
                continue
            if score__lte and total_score > score__lte:
                continue
            user_data["total_score"] = total_score
            user_data["submission_date"] = grade.created
            object_list.append(user_data)

        context = self.get_context_data(
            object_list=object_list,
            spc_list=spc_list,
            unit_list=unit_list,
            max_score=max_score,
            workspace_url=settings.SLACK_WORKSPACE,
        )
        return self.render_to_response(context)


class InstructorUnitListView(InstructorViewsMixin, BaseUnitListView):
    template_name = "academy/instructor/unit_list.html"
    detail_view_name = "academy:instructor-unit-detail"


class InstructorUnitDetailView(InstructorViewsMixin, BaseUnitDetailView):
    template_name = "academy/instructor/unit_detail.html"
