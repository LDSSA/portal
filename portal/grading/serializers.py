from rest_framework import serializers  # noqa: D100

from portal.academy import models
from portal.applications.models import Challenge, Submission


class GradeSerializer(serializers.ModelSerializer):  # noqa: D101
    notebook = serializers.FileField(source="feedback")

    class Meta:  # noqa: D106
        model = models.Grade
        fields = (
            "score",
            "status",
            "message",
            "notebook",
        )


class ChecksumSerializer(serializers.ModelSerializer):  # noqa: D101
    unit = serializers.SlugField(source="code")

    class Meta:  # noqa: D106
        model = models.Unit
        fields = (
            "unit",
            "checksum",
        )

    def update(self, instance, validated_data):  # noqa: ANN001, ANN101, ANN201, D102
        old_checksum = instance.checksum
        instance = super().update(instance, validated_data)

        if old_checksum != instance.checksum:
            for grade in models.Grade.objects.filter(unit=instance, status="graded"):
                grade.status = "out-of-date"
                grade.save()

        return instance


class AdmissionsGradeSerializer(serializers.ModelSerializer):  # noqa: D101
    notebook = serializers.FileField(source="feedback")

    class Meta(GradeSerializer.Meta):  # noqa: D106
        model = Submission


class AdmissionsChecksumSerializer(serializers.ModelSerializer):  # noqa: D101
    unit = serializers.SlugField(source="code")

    class Meta:  # noqa: D106
        model = Challenge
        fields = (
            "unit",
            "checksum",
        )
