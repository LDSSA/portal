from rest_framework import serializers

from . import models


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Grade
        fields = (
            'score',
            'status',
            'message',
            'notebook',
        )


class ChecksumSerializer(serializers.ModelSerializer):
    unit = serializers.SlugField(source='code')

    class Meta:
        model = models.Unit
        fields = (
            'unit',
            'checksum',
        )

    def update(self, instance, validated_data):
        old_checksum = instance.checksum
        instance = super().update(instance, validated_data)

        if old_checksum != instance.checksum:
            for grade in models.Grade.objects.filter(unit=instance,
                                                     status='graded'):
                grade.status = 'out-of-date'
                grade.save()

        return instance
