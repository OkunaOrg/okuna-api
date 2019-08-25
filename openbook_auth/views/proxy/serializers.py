from rest_framework import serializers


class ProxyAuthSerializer(serializers.Serializer):
    url = serializers.CharField(
        required=False,
        allow_blank=True)
