from rest_framework import serializers

from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_circles.models import Circle
from openbook_common.validators import hex_color_validator


class CreateCircleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=CIRCLE_MAX_LENGTH, required=True, allow_blank=False)
    color = serializers.CharField(max_length=COLOR_ATTR_MAX_LENGTH, required=True, allow_blank=False,
                                  validators=[hex_color_validator])


class CircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
        )
