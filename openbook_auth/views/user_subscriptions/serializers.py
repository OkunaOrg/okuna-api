from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import \
    IsConnectedField, IsSubscribedField


class GetUserSubscriptionsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class SearchUserSubscriptionsSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class UserSubscriptionsUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class UserSubscriptionsUserProfileSerializer(serializers.ModelSerializer):
    badges = UserSubscriptionsUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class UserSubscriptionsUserSerializer(serializers.ModelSerializer):
    profile = UserSubscriptionsUserProfileSerializer(many=False)
    is_subscribed = IsSubscribedField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_subscribed',
            'is_connected'
        )
