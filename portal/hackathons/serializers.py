from rest_framework import serializers


class SubmissionSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    data = serializers.JSONField()
