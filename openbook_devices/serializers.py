from django.conf import settings
from rest_framework import serializers

from openbook_devices.models import Device
from openbook_devices.validators import device_id_exists


class GetDevicesSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    max_id = serializers.IntegerField(
        required=False,
    )


class GetDevicesDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            'id',
            'uuid',
            'one_signal_player_id',
            'notifications_enabled'
        )


class GetDeviceSerializer(serializers.Serializer):
    device_id = serializers.IntegerField(validators=[device_id_exists])


class DeleteDeviceSerializer(serializers.Serializer):
    device_id = serializers.IntegerField(validators=[device_id_exists])


class UpdateDeviceSerializer(serializers.Serializer):
    device_id = serializers.IntegerField(validators=[device_id_exists])
    name = serializers.CharField(max_length=settings.DEVICE_NAME_MAX_LENGTH, required=False, allow_blank=False, )
    notifications_enabled = serializers.BooleanField(required=False)
    one_signal_player_id = serializers.CharField(required=False)


class CreateDeviceSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    name = serializers.CharField(max_length=settings.DEVICE_NAME_MAX_LENGTH, required=False, allow_blank=False, )
    notifications_enabled = serializers.BooleanField(required=False)
    one_signal_player_id = serializers.CharField()
