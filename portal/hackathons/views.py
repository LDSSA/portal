import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic
from rest_framework import generics

from portal.academy.views import StudentMixin, InstructorMixin
from portal.hackathons import models, serializers, forms, services
from portal.capstone.models import StudentApi, Capstone


logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class LeaderboardView(LoginRequiredMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.all()
    template_name = 'hackathons/leaderboard.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        submissions = {}
        # If scores are to be descending (higher is top score)
        ordering = '-' if self.object.descending else ''
        for submission in (models.Submission.objects
                           .filter(hackathon=self.object)
                           .order_by(ordering + 'score', 'created')):
            if submission.content_object not in submissions:
                submissions[submission.content_object] = submission

        context = self.get_context_data(object=self.object,
                                        submissions=submissions)

        return self.render_to_response(context)


class MockSubmission:
    def __init__(self, score):
        self.score = score


class FrankenLeaderboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'hackathons/leaderboard.html'

    def get(self, request, *args, **kwargs):
        submissions = {}
        # Get the teams for this hackathon
        hckt06 = models.Hackathon.objects.filter(code='HCKT06')
        hckt06_teams = hckt06.teams.all()
        capstone = Capstone.objects.get(name='Hackthon 6')

        for team in hckt06_teams:
            # Get the score of the student with the highest score
            # this will be the team score
            scores = []
            for student in team.students.all():
                student_api = StudentApi.objects.get(capstone=capstone,
                                                     student=student)
                scores.append(student_api.score)

            try:
                score = max(scores)
            except ValueError:
                # Team has not registered an app
                score = 0
            if score == 0:
                continue
            submissions[team] = MockSubmission(0)

        context = self.get_context_data(submissions=submissions)
        return self.render_to_response(context)


class StudentHackathonListView(StudentMixin, generic.ListView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/student/hackathon_list.html'


# noinspection PyUnusedLocal
class StudentHackathonDetailView(StudentMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/student/hackathon_detail.html'

    # noinspection PyAttributeOutsideInit
    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)
        hackathon = self.object

        attendance, _ = models.Attendance.objects.get_or_create(
            student=self.request.user,
            hackathon=hackathon)

        team = models.Team.objects.filter(
            hackathon=hackathon,
            students=self.request.user,
        ).first()

        return hackathon, attendance, team

    def get(self, request, *args, **kwargs):
        hackathon, attendance, team = self.get_object()
        context = self.get_context_data(
            hackathon=hackathon,
            attendance=attendance,
            team=team,
            attendance_form=forms.StudentAttendanceForm(instance=attendance),
            team_form=forms.TeamForm(instance=team),
            submit_form=forms.SubmitForm(),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        hackathon, attendance, team = self.get_object()

        if 'attendance' in request.POST:
            attendance_form = forms.StudentAttendanceForm(request.POST,
                                                          instance=attendance)
            if attendance_form.is_valid():
                attendance_form.save()

        elif 'team' in request.POST:
            team_form = forms.TeamForm(request.POST,
                                       instance=team)
            if team_form.is_valid():
                team_form.save()

        elif 'submit' in request.POST:
            try:
                score = services.submission(hackathon,
                                            request.user,
                                            request.FILES['data'])
            except services.ValidationError as exc:
                messages.add_message(request,
                                     messages.ERROR,
                                     str(exc.__cause__ or exc))  # Use root exception if defined
            except Exception as exc:
                messages.add_message(request,
                                     messages.ERROR,
                                     "An unexpected error occurred! Oh noes! The dev-ops team has been notified.")
                logger.exception("Unhandled Exception during scoring")

            else:
                messages.add_message(request,
                                     messages.SUCCESS,
                                     "Score: %s" % score)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hackathons:student-hackathon-detail',
                       args=(self.object.pk, ))


class InstructorHackathonListView(InstructorMixin, generic.ListView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/instructor/hackathon_list.html'


class InstructorHackathonSettingsView(InstructorMixin, generic.UpdateView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/instructor/hackathon_settings.html'
    form_class = forms.InstructorHackathonForm

    def get_success_url(self):
        return reverse('hackathons:instructor-hackathon-settings',
                       args=(self.object.pk, ))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class InstructorHackathonAdminView(InstructorMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/instructor/hackathon_admin.html'

    def get_object_list(self):
        object_list = []
        attendance = models.Attendance.objects.filter(hackathon=self.object)
        for att in attendance:
            try:
                team = att.student.hackathon_teams.get(
                    hackathon=att.hackathon)
            except ObjectDoesNotExist:
                team = None

            object_list.append({
                'hackathon_team_id': team.hackathon_team_id if team is not None else 0,
                'student': att.student,
                'team': team,
                'attendance': att})
        object_list = sorted(object_list, key=lambda x: x['hackathon_team_id'])
        return object_list

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        object_list = self.get_object_list()
        context = self.get_context_data(object=self.object,
                                        object_list=object_list)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        object_list = self.get_object_list()

        new_status = request.POST.get('status')
        cur_status = self.object.status
        logger.debug("new_status: %s cur_status: %s",
                     new_status, cur_status)

        self.object.status = new_status
        self.object.save()

        if (cur_status == 'marking_presences'
                and new_status == 'generating_teams'):
            for item in object_list:
                logger.info(request.POST)
                logger.info(item['student'].username)
                logger.info(item['student'].username in request.POST)
                if item['student'].username in request.POST:
                    item['attendance'].present = True
                else:
                    item['attendance'].present = False
                item['attendance'].save()

        elif (new_status == 'generating_teams'
              and cur_status == 'generating_teams'):
            self.object.teams.all().delete()
            services.generate_teams(self.object,
                                    self.object.team_size,
                                    self.object.max_team_size,
                                    self.object.max_teams)

        elif new_status == 'taking_attendance':
            for user in get_user_model().objects.filter(student=True):
                attendance, _ = models.Attendance.objects.get_or_create(
                    student=user,
                    hackathon=self.object)

        # Delete test submissions
        elif new_status == 'closed' and cur_status == 'closed':
            models.Submission.objects.filter(hackathon=self.object).delete()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hackathons:instructor-hackathon-admin',
                       args=(self.object.pk, ))


# noinspection PyUnusedLocal
class InstructorHackathonDetailView(InstructorMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/instructor/hackathon_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(
            hackathon=self.object,
            submit_form=forms.SubmitForm(),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            score = services.submission(self.object,
                                        request.user,
                                        request.FILES['data'])
        except Exception as exc:
            messages.add_message(request, messages.ERROR, str(exc))

        else:
            messages.add_message(request,
                                 messages.SUCCESS,
                                 "Score: %s" % score)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hackathons:instructor-hackathon-detail',
                       args=(self.object.pk, ))


class HackathonSetupView(generics.UpdateAPIView):
    queryset = models.Hackathon.objects.all()
    serializer_class = serializers.HackathonSerializer
    lookup_url_kwarg = 'pk'
    lookup_field = 'pk__iexact'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
