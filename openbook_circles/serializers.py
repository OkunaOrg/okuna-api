from rest_framework import serializers

from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.validators import hex_color_validator


class CreateCircleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=True, allow_blank=False)
    color = serializers.CharField(max_length=COLOR_ATTR_MAX_LENGTH, required=True, allow_blank=False,
                                  validators=[hex_color_validator])


class DeleteCircleSerializer(serializers.Serializer):
    circle_id = serializers.IntegerField(required=True, validators=[circle_id_exists])


class CircleUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class CircleUserSerializer(serializers.ModelSerializer):
    profile = CircleUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'profile',
        )


class CircleSerializer(serializers.ModelSerializer):
    users = CircleUserSerializer(many=True)

    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
            'users'
        )
