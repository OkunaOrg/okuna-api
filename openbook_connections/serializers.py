from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_username_exists, username_characters_validator
from openbook_circles.validators import circle_id_exists

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
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])


class ConnectionUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class ConnectionUserSerializer(serializers.ModelSerializer):
    profile = ConnectionUserProfileSerializer(many=False)
    is_connected = serializers.SerializerMethodField()

    def get_is_connected(self, obj):
        request = self.context.get('request')

        if not request.user.is_anonymous:
            if request.user.pk == obj.pk:
                return False
            return request.user.is_connected_with_user_with_id(obj.pk)

        return False

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'is_connected'
        )


class ConnectionSerializer(serializers.ModelSerializer):
    target_user = ConnectionUserSerializer(many=False)

    class Meta:
        model = Connection
        fields = (
            'id',
            'user',
            'circle',
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
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])


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
    circle_id = serializers.IntegerField(required=False, validators=[circle_id_exists])
