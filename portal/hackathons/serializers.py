from rest_framework import serializers

from portal.hackathons import models


class HackathonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Hackathon
        fields = ['script_file', 'data_file']
