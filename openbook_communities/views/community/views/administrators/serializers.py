from django.conf import settings
from rest_framework import serializers

from openbook_auth.validators import username_characters_validator, user_username_exists


class AddCommunityAdministratorSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists])


class RemoveCommunityAdministratorSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists])


class GetCommunityAdministratorsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    query = serializers.CharField(
        max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
        allow_blank=False,
        required=True
    )
