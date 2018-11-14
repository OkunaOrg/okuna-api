from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_id_exists
from openbook_circles.validators import circle_id_exists

from openbook_connections.models import Connection


class ConnectWithUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
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

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
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
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])


class UpdateConnectionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])


class ConfirmConnectionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
    circle_id = serializers.IntegerField(required=False, validators=[circle_id_exists])
