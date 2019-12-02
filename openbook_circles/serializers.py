from django.conf import settings
from rest_framework import serializers

from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import IsFullyConnectedField, IsPendingConnectionConfirmation
from openbook_common.validators import hex_color_validator


class CreateCircleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=True, allow_blank=False)
    color = serializers.CharField(max_length=COLOR_ATTR_MAX_LENGTH, required=True, allow_blank=False,
                                  validators=[hex_color_validator])


class DeleteCircleSerializer(serializers.Serializer):
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])


class UpdateCircleSerializer(serializers.Serializer):
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=False, allow_blank=False)
    color = serializers.CharField(max_length=COLOR_ATTR_MAX_LENGTH, required=False, allow_blank=False,
                                  validators=[hex_color_validator])
    usernames = serializers.ListSerializer(
        required=False,
        allow_empty=True,
        child=serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                    allow_blank=False,
                                    required=False,
                                    validators=[username_characters_validator, user_username_exists])
    )


class CircleUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class CircleUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    badges = CircleUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'badges'
        )


class CircleUserSerializer(serializers.ModelSerializer):
    profile = CircleUserProfileSerializer(many=False)
    is_fully_connected = IsFullyConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'profile',
            'is_fully_connected',
        )


class GetCirclesCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
            'users_count'
        )


class GetCircleCircleSerializer(serializers.ModelSerializer):
    users = CircleUserSerializer(many=True)

    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
            'users',
            'users_count'
        )


class CircleNameCheckSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=True, allow_blank=False, validators=[])
