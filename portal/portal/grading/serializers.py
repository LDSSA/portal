from rest_framework import serializers

from portal.academy import models
from portal.applications.models import Challenge, Submission


class GradeSerializer(serializers.ModelSerializer):
    notebook = serializers.FileField(source="feedback")

    def update(self, instance, validated_data):
        # Callbacks may only change grading output, never staff deadline decisions.
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if validated_data:
            instance.save(update_fields=list(validated_data))
        return instance

    class Meta:
        model = models.Grade
        fields = (
            "score",
            "status",
            "message",
            "notebook",
        )


class ChecksumSerializer(serializers.ModelSerializer):
    unit = serializers.SlugField(source="code")

    class Meta:
        model = models.Unit
        fields = (
            "unit",
            "checksum",
        )

    def update(self, instance, validated_data):
        old_checksum = instance.checksum
        instance = super().update(instance, validated_data)

        if old_checksum != instance.checksum:
            for grade in models.Grade.objects.filter(unit=instance, status="graded"):
                grade.status = "out-of-date"
                grade.save(update_fields=["status"])

        return instance


class AdmissionsGradeSerializer(serializers.ModelSerializer):
    notebook = serializers.FileField(source="feedback")

    class Meta(GradeSerializer.Meta):
        model = Submission


class AdmissionsChecksumSerializer(serializers.ModelSerializer):
    unit = serializers.SlugField(source="code")

    class Meta:
        model = Challenge
        fields = (
            "unit",
            "checksum",
        )
