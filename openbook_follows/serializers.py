from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_id_exists

from openbook_follows.models import Follow


class FollowUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
    list_id = serializers.IntegerField(required=False)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class FollowSerializer(serializers.ModelSerializer):
    followed_user = UserSerializer(many=False)

    class Meta:
        model = Follow
        fields = (
            'id',
            'user',
            'list',
            'followed_user',
        )


class DeleteFollowSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)


class UpdateFollowSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    list_id = serializers.IntegerField(required=True)
