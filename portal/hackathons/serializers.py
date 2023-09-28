from rest_framework import serializers  # noqa: D100

from portal.hackathons import models


class HackathonSerializer(serializers.ModelSerializer):  # noqa: D101
    class Meta:  # noqa: D106
        model = models.Hackathon
        fields = ["script_file", "data_file"]
