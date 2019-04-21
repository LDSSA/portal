from rest_framework import serializers

from . import models
from portal.users.models import User


class GradeSerializer(serializers.ModelSerializer):
    username = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        source='student',
    )
    unit = serializers.SlugRelatedField(
        slug_field='code',
        queryset=models.Unit.objects.all(),
    )
    notebook = serializers.FileField()

    class Meta:
        model = models.Grade
        fields = (
            'unit',
            'username',
            'score',
            'status',
            'message',
            'notebook',
        )


class ChecksumSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Unit
        fields = (
            'code',
            'checksum',
        )
        read_only_fields = (
            'code',
        )

