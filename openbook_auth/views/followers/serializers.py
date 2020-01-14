from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import \
    IsFollowingField, IsConnectedField, IsFollowedField


class GetFollowersSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class SearchFollowersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class FollowersUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class FollowersUserProfileSerializer(serializers.ModelSerializer):
    badges = FollowersUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class FollowersUserSerializer(serializers.ModelSerializer):
    profile = FollowersUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    is_connected = IsConnectedField()
    is_followed = IsFollowedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'is_connected',
            'is_followed'
        )
