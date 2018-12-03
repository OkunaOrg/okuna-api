from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, user_username_exists

from openbook_follows.models import Follow


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
    list_id = serializers.IntegerField(required=False)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class FollowUserSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    def get_is_following(self, obj):
        request = self.context.get('request')
        return request.user.is_following_user_with_id(obj.pk)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'is_following',
        )


class FollowSerializer(serializers.ModelSerializer):
    followed_user = FollowUserSerializer(many=False)

    class Meta:
        model = Follow
        fields = (
            'id',
            'user',
            'list',
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
    list_id = serializers.IntegerField(required=True)
