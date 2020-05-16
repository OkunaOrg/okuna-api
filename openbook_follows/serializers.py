from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import IsFollowingField, FollowListsField

from openbook_follows.models import Follow
from openbook_lists.models import List
from openbook_lists.validators import list_id_exists


class RequestToFollowUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


class ApproveUserFollowRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


class RejectUserFollowRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


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


class UserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    badges = UserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'badges'
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


class ReceivedFollowRequestsRequestSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
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
