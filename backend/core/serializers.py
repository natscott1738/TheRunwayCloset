from rest_framework import serializers

class IDSerializer(serializers.Serializer):
    id = serializers.UUIDField()
