# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_devices.serializers import GetDevicesSerializer, GetDevicesDeviceSerializer, \
    DeleteDeviceSerializer, CreateDeviceSerializer, UpdateDeviceSerializer


class Devices(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request):
        serializer = CreateDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        name = data.get('name')
        uuid = data.get('uuid')

        user = request.user

        with transaction.atomic():
            device = user.create_device(name=name, uuid=uuid)

        response_serializer = GetDevicesDeviceSerializer(device, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetDevicesSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        devices = user.get_devices(max_id=max_id).order_by('-created')[:count]

        response_serializer = GetDevicesDeviceSerializer(devices, many=True,
                                                         context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user

        with transaction.atomic():
            user.delete_devices()

        return Response(status=status.HTTP_200_OK)


class DeviceItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, device_uuid):
        user = request.user

        device = user.get_device_with_uuid(device_uuid=device_uuid)

        response_serializer = GetDevicesDeviceSerializer(device,
                                                         context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, device_uuid):
        request_data = normalise_request_data(request.data)
        request_data['device_uuid'] = device_uuid

        serializer = UpdateDeviceSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        name = data.get('name')

        user = request.user

        with transaction.atomic():
            device = user.update_device_with_uuid(device_uuid=device_uuid, name=name)

        response_serializer = GetDevicesDeviceSerializer(device, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, device_uuid):
        serializer = DeleteDeviceSerializer(data={'device_uuid': device_uuid})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_device_with_uuid(device_uuid=device_uuid)

        return Response(status=status.HTTP_200_OK)
