from django.conf import settings
from rest_framework import serializers

from openbook_moderation.views.validators import moderated_object_id_exists


class EditModeratedObjectSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=settings.MODERATED_OBJECT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)
    verified = serializers.BooleanField(required=False,
                                        allow_blank=False)
    approved = serializers.BooleanField(required=False,
                                        allow_blank=False)
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )


class SubmitModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.UUIDField(
        validators=[moderated_object_id_exists],
        required=True,
    )
