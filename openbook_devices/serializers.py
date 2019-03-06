from django.conf import settings
from rest_framework import serializers

from openbook_devices.models import Device


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
        )


class GetDeviceSerializer(serializers.Serializer):
    device_uuid = serializers.CharField()


class DeleteDeviceSerializer(serializers.Serializer):
    device_uuid = serializers.CharField()


class UpdateDeviceSerializer(serializers.Serializer):
    device_uuid = serializers.CharField()
    name = serializers.CharField(max_length=settings.DEVICE_NAME_MAX_LENGTH, required=False, allow_blank=False, )


class CreateDeviceSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    name = serializers.CharField(max_length=settings.DEVICE_NAME_MAX_LENGTH, required=False, allow_blank=False, )
