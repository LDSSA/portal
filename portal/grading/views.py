import logging

from django.http import HttpResponse
from rest_framework import generics

from . import serializers
from portal.academy import models
from portal.applications.models import Challenge, Submission


logger = logging.getLogger(__name__)


class AcademyGradingView(generics.RetrieveUpdateAPIView):
    """Receive notebook grade"""

    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer


class AcademyChecksumView(generics.RetrieveUpdateAPIView):
    """Receive and retrieve notebook checksum"""

    lookup_field = "code"
    queryset = models.Unit.objects.all()
    serializer_class = serializers.ChecksumSerializer


class AdmissionsGradingView(generics.RetrieveUpdateAPIView):
    """Receive notebook grade"""

    queryset = Submission.objects.all()
    serializer_class = serializers.AdmissionsGradeSerializer


class AdmissionsChecksumView(generics.RetrieveUpdateAPIView):
    """Receive and retrieve notebook checksum"""

    queryset = Challenge.objects.all()
    serializer_class = serializers.AdmissionsChecksumSerializer


class AdmissionsNotebookDownload(generics.RetrieveUpdateAPIView):
    """Receive and retrieve notebook checksum"""

    queryset = Submission.objects.all()

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        response = HttpResponse(
            obj.notebook.read(), content_type="application/vnd.jupyter"
        )
        response[
            "Content-Disposition"
        ] = "attachment; filename=Exercise notebook.ipynb"
        return response
