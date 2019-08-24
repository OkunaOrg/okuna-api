from rest_framework import serializers

from openbook_common.helpers import normalise_url


class ProxyAuthSerializer(serializers.Serializer):
    url = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[normalise_url])
