import logging
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from portal.academy.views import StudentMixin, InstructorMixin
from portal.hackathons import models, serializers, forms, services


logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@api_view(http_method_names=['POST'])
def submission(request, *args, **kwargs):
    code = kwargs['code']
    serializer = serializers.SubmissionSerializer(
        data=request.data,
        context={'request': request})
    serializer.is_valid(raise_exception=True)

    token = serializer.validated_data['token']
    team = models.Team.objects.get(hackathon__code=code, token=token)

    if team.hackathon.open:
        if not team.hackathon.complete:
            if team.submissions >= team.hackathon.max_submissions:
                raise ValidationError({
                    'non_field_errors': ['Submission limit reached.']})
    else:
        raise ValidationError({
            'non_field_errors': ['Hackathon not open.']})

    y_pred = serializer.validated_data['data']
    y_true = json.loads(team.hackathon.y_true)

    exec(team.hackathon.scoring_fcn)
    # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
    score = score(y_pred, y_true)

    if score is None:
        raise RuntimeError("Unexpected error")

    if team.hackathon.descending:
        if score > team.score:
            team.score = score
    else:
        if score < team.score:
            team.score = score

    team.submissions += 1
    team.save()

    return Response({'score': score})


# noinspection PyAttributeOutsideInit
class LeaderboardView(LoginRequiredMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.all()
    template_name = 'hackathons/leaderboard.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        ordering = '-' if self.object.descending else ''
        teams = (models.Team.objects.filter(hackathon=self.object)
                 .order_by(ordering + 'score'))
        context = self.get_context_data(object=self.object,
                                        teams=teams)

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
        return reverse('hackathons:instructor-hackathon-detail',
                       args=(self.object.pk, ))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class InstructorHackathonDetailView(InstructorMixin, generic.DetailView):
    model = models.Hackathon
    queryset = models.Hackathon.objects.order_by('code')
    template_name = 'hackathons/instructor/hackathon_detail.html'

    def get_object_list(self):

        teams = (models.Team.objects.filter(hackathon=self.object)
                 .order_by('hackathon_team_id'))
        teams_exist = teams.exists()
        object_list = []
        if teams_exist:
            for team in teams:
                for student in team.students.all():
                    object_list.append({
                        'student': student,
                        'team': team,
                        'attendance': student.attendance.filter(
                            hackathon=self.object)[0],
                    })

        else:
            attendance = models.Attendance.objects.filter(
                hackathon=self.object)
            for att in attendance:
                object_list.append({'student': att.student,
                                    'attendance': att})

        return object_list, teams_exist

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        object_list, teams_exist = self.get_object_list()
        context = self.get_context_data(object=self.object,
                                        object_list=object_list,
                                        teams_exist=teams_exist)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        object_list, teams_exist = self.get_object_list()

        # Instructor marking students as present/not present
        if 'attendance' in request.POST:
            for item in object_list:
                logger.info(item['student'].username)
                logger.info(item['student'].username in request.POST)
                if item['student'].username in request.POST:
                    item['attendance'].present = True
                else:
                    item['attendance'].present = False
                item['attendance'].save()

        else:
            new_status = request.POST.get('status')
            cur_status = self.object.status

            self.object.status = new_status
            self.object.save()

            if new_status == 'generating_teams':
                if cur_status in ('marking_presences', 'generating_teams'):
                    self.object.teams.all().delete()
                    services.generate_teams(self.object,
                                            self.object.team_size,
                                            self.object.max_team_size,
                                            self.object.max_teams)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hackathons:instructor-hackathon-detail',
                       args=(self.object.pk, ))
