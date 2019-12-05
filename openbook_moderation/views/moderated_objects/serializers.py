from django.conf import settings
from rest_framework import serializers

from openbook_communities.validators import community_name_exists, community_name_characters_validator
from openbook_moderation.models import ModeratedObject


class GetGlobalModeratedObjectsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    types = serializers.MultipleChoiceField(
        choices=[ModeratedObject.OBJECT_TYPE_POST, ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                 ModeratedObject.OBJECT_TYPE_COMMUNITY,
                 ModeratedObject.OBJECT_TYPE_USER,
                 ModeratedObject.OBJECT_TYPE_HASHTAG, ], required=False)
    statuses = serializers.MultipleChoiceField(
        choices=[ModeratedObject.STATUS_REJECTED, ModeratedObject.STATUS_PENDING,
                 ModeratedObject.STATUS_APPROVED, ], required=False)
    verified = serializers.BooleanField(
        required=False,
    )
    approved = serializers.BooleanField(
        required=False,
    )


class GetCommunityModeratedObjectsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    types = serializers.MultipleChoiceField(
        choices=[ModeratedObject.OBJECT_TYPE_POST, ModeratedObject.OBJECT_TYPE_POST_COMMENT, ], required=False)
    statuses = serializers.MultipleChoiceField(
        choices=[ModeratedObject.STATUS_REJECTED, ModeratedObject.STATUS_PENDING,
                 ModeratedObject.STATUS_APPROVED, ], required=False)
    verified = serializers.BooleanField(
        required=False,
    )
    approved = serializers.BooleanField(
        required=False,
    )
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])
