from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import Http404
from django.views.generic import DetailView, ListView, RedirectView
from rest_framework import generics
from rest_framework.settings import import_from_string

from portal.academy import models, serializers


class InstructorMixin(AccessMixin):
    """Verify that the current user is an instructor."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.student:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class StudentMixin(AccessMixin):
    """Verify that the current user is a student."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.student:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class HomeRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.student:
            self.pattern_name = 'academy:student-unit-list'

        else:
            self.pattern_name = 'academy:instructor-user-list'

        return super().get_redirect_url(*args, **kwargs)


class StudentUnitListView(StudentMixin, ListView):
    model = models.Unit
    queryset = models.Unit.objects.order_by('due_date')
    template_name = 'academy/student/unit_list.html'

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


class StudentUnitDetailView(StudentMixin, DetailView):
    model = models.Unit
    template_name = 'academy/student/unit_detail.html'

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


class InstructorUserListView(InstructorMixin, ListView):
    model = get_user_model()
    queryset = get_user_model().objects.filter(student=True)
    template_name = 'academy/instructor/user_list.html'

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()

        specializations = models.Specialization.objects.order_by('code')
        spc_list = []
        unit_list = []
        max_score = 0
        for spc in specializations:
            qs = (models.Unit.objects
                  .filter(specialization=spc)
                  .order_by('due_date'))
            spc_list.append(spc)
            max_score += qs.count() * 20
            if qs.exists():
                unit_list += list(qs)
            else:
                unit_list += [None]

        object_list = []
        for user in self.object_list:
            total_score = 0
            user_data = {'user': user, 'grades': [], 'total_score': 0}
            for unit in unit_list:
                if unit is None:
                    user_data['grades'].append(None)

                else:
                    grade, _ = models.Grade.objects.get_or_create(student=user,
                                                                  unit=unit)
                    if grade.status == 'graded':
                        total_score += grade.score
                    user_data['grades'].append(grade)
            user_data['total_score'] = total_score
            object_list.append(user_data)

        context = self.get_context_data(object_list=object_list,
                                        spc_list=spc_list,
                                        unit_list=unit_list,
                                        max_score=max_score)
        return self.render_to_response(context)


class GradingView(generics.RetrieveUpdateAPIView):
    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer

    def get_object(self):
        user = get_user_model().objects.get(
            username=self.kwargs.get('username'))
        unit = models.Unit.objects.get(code=self.kwargs.get('unit').upper())
        grade, _ = models.Grade.objects.get_or_create(
            student=user,
            unit=unit)

        # May raise a permission denied
        self.check_object_permissions(self.request, grade)

        return grade


class ChecksumView(generics.RetrieveUpdateAPIView):
    queryset = models.Unit.objects.all()
    serializer_class = serializers.ChecksumSerializer

    def get_object(self):
        try:
            obj = super().get_object()

        except Http404:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            uppercase = self.kwargs[lookup_url_kwarg].upper()
            self.kwargs[lookup_url_kwarg] = uppercase
            obj = super().get_object()

        return obj
