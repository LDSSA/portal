from rest_framework import serializers  # noqa: D100

from . import models


class InstructorsViewFiltersSerializer(serializers.Serializer):  # noqa: D101
    user_id = serializers.IntegerField(required=False)
    spc_code = serializers.CharField(required=False)
    unit_code = serializers.CharField(required=False)
    grade_status = serializers.ChoiceField(required=False, choices=models.Grade.STATUSES)
    score__gte = serializers.FloatField(required=False)
    score__lte = serializers.FloatField(required=False)
    can_graduate = serializers.BooleanField(required=False)
