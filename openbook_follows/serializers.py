from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_common.serializers_fields.user import IsFollowingField, FollowListsField

from openbook_follows.models import Follow
from openbook_lists.models import List
from openbook_lists.validators import list_id_exists


class FollowUserRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )
    lists_ids = serializers.ListSerializer(
        required=False,
        child=serializers.IntegerField(validators=[list_id_exists])
    )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class FollowUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = (
            'id',
            'name',
        )


class FollowUserSerializer(serializers.ModelSerializer):
    is_following = IsFollowingField()
    follow_lists = FollowListsField(list_serializer=FollowUserListSerializer)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'is_following',
            'follow_lists'
        )


class FollowSerializer(serializers.ModelSerializer):
    followed_user = FollowUserSerializer(many=False)

    class Meta:
        model = Follow
        fields = (
            'id',
            'user',
            'lists',
            'followed_user',
        )


class DeleteFollowSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


class UpdateFollowSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )
    lists_ids = serializers.ListSerializer(
        required=False,
        child=serializers.IntegerField(validators=[list_id_exists])
    )
