from rest_framework import serializers
from django.conf import settings


class CommentPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)
