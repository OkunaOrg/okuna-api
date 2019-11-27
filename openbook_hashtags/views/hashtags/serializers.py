from django.conf import settings
from rest_framework import serializers

from openbook_hashtags.models import Hashtag


class SearchHashtagsSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )


class SearchHashtagsHashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = (
            'id',
            'name',
            'color',
            'image'
        )
