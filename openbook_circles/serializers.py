from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_circles.models import Circle
from openbook_circles.validators import circle_name_not_taken_for_user_validator, circle_id_exists
from openbook_common.validators import hex_color_validator
from django.utils.translation import ugettext_lazy as _


class CreateCircleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=True, allow_blank=False,
                                 validators=[])
    color = serializers.CharField(max_length=COLOR_ATTR_MAX_LENGTH, required=True, allow_blank=False,
                                  validators=[hex_color_validator])

    def validate_name(self, name):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            circle_name_not_taken_for_user_validator(name, user)
            return name
        else:
            raise ValidationError(
                _('A user is required.'),
            )


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
