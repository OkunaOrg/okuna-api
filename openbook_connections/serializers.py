from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_username_exists, username_characters_validator
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import IsConnectedField, ConnectedCirclesField, IsFollowingField, \
    IsPendingConnectionConfirmation, IsFullyConnectedField, AreNewPostNotificationsEnabledForUserField

from openbook_connections.models import Connection


class ConnectWithUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )
    circles_ids = serializers.ListSerializer(
        child=serializers.IntegerField(required=True, validators=[circle_id_exists])
    )


class ConnectionUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class ConnectionUserProfileSerializer(serializers.ModelSerializer):
    badges = ConnectionUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'badges'
        )


class ConnectionUserCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
            'users_count'
        )


class ConnectionUserSerializer(serializers.ModelSerializer):
    profile = ConnectionUserProfileSerializer(many=False)
    is_connected = IsConnectedField()
    is_following = IsFollowingField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    connected_circles = ConnectedCirclesField(circle_serializer=ConnectionUserCircleSerializer)
    is_pending_connection_confirmation = IsPendingConnectionConfirmation()
    is_fully_connected = IsFullyConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'is_connected',
            'is_fully_connected',
            'is_following',
            'are_new_post_notifications_enabled',
            'connected_circles',
            'is_pending_connection_confirmation'
        )


class ConnectionSerializer(serializers.ModelSerializer):
    target_user = ConnectionUserSerializer(many=False)

    class Meta:
        model = Connection
        fields = (
            'id',
            'user',
            'circles',
            'target_user',
        )


class DisconnectFromUserSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


class UpdateConnectionSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )
    circles_ids = serializers.ListSerializer(
        child=serializers.IntegerField(required=True, validators=[circle_id_exists])
    )


class ConfirmConnectionSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )
    circles_ids = serializers.ListSerializer(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists])
    )
