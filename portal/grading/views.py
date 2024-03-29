import logging  # noqa: D100

from django.http import HttpResponse
from rest_framework import generics

from portal.academy import models
from portal.academy.services import check_complete_specialization
from portal.applications.models import Challenge, Submission

from . import serializers

logger = logging.getLogger(__name__)


class AcademyGradingView(generics.RetrieveUpdateAPIView):

    """Receive notebook grade."""  # noqa: D211

    queryset = models.Grade.objects.all()
    serializer_class = serializers.GradeSerializer

    def update(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, D102
        update_result = super().update(request, *args, **kwargs)

        grade = self.get_object()
        user = grade.user
        spec = grade.unit.specialization

        # Check attendance for next hackathon based on last grade received
        user.can_attend_next = check_complete_specialization(user, spec)
        user.save()

        return update_result


class CaseInsensitiveGetObjectMixin:  # noqa: D101
    def get_object(self):  # noqa: ANN101, ANN201
        """Return the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        if lookup_url_kwarg not in self.kwargs:
            msg = 'Expected view {} to be called with a URL keyword argument named "{}". Fix your URL conf, or set the `.lookup_field` attribute on the view correctly.'.format(
                self.__class__.__name__,
                lookup_url_kwarg,
            )
            raise ValueError(
                msg,
            )

        filter_kwargs = {f"{self.lookup_field}__iexact": self.kwargs[lookup_url_kwarg]}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class AcademyChecksumView(CaseInsensitiveGetObjectMixin, generics.RetrieveUpdateAPIView):

    """Receive and retrieve notebook checksum."""  # noqa: D211

    queryset = models.Unit.objects.all()
    serializer_class = serializers.ChecksumSerializer


class AdmissionsGradingView(CaseInsensitiveGetObjectMixin, generics.RetrieveUpdateAPIView):

    """Receive notebook grade."""  # noqa: D211

    queryset = Submission.objects.all()
    serializer_class = serializers.AdmissionsGradeSerializer


class AdmissionsChecksumView(CaseInsensitiveGetObjectMixin, generics.RetrieveUpdateAPIView):

    """Receive and retrieve notebook checksum."""  # noqa: D211

    queryset = Challenge.objects.all()
    serializer_class = serializers.AdmissionsChecksumSerializer


class AdmissionsNotebookDownload(CaseInsensitiveGetObjectMixin, generics.RetrieveUpdateAPIView):

    """Receive and retrieve notebook checksum."""  # noqa: D211

    queryset = Submission.objects.all()

    def get(  # noqa: ANN201, D102
        self, request, *args, **kwargs  # noqa: ANN001, ANN002, ANN003, ANN101, ARG002
    ):  # noqa: ANN001, ANN002, ANN003, ANN101, ANN201, ARG002, D102
        obj = self.get_object()
        response = HttpResponse(obj.notebook.read(), content_type="application/vnd.jupyter")
        response["Content-Disposition"] = "attachment; filename=Exercise notebook.ipynb"
        return response
