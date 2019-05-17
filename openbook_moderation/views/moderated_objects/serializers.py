from rest_framework import serializers

from openbook_moderation.models import ModeratedObject


class GetModeratedObjectsSerializer(serializers.Serializer):
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
                 ModeratedObject.OBJECT_TYPE_USER], required=False)
    statuses = serializers.MultipleChoiceField(
        choices=[ModeratedObject.STATUS_REJECTED, ModeratedObject.STATUS_PENDING,
                 ModeratedObject.STATUS_APPROVED, ], required=False)
    verified = serializers.BooleanField(
        required=False,
    )
    approved = serializers.BooleanField(
        required=False,
    )
