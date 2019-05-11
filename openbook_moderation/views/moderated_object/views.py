from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ModeratedObjectItem(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, reported_object_id):
        request_data = request.data.copy()
        request_data['reported_object_id'] = reported_object_id

        serializer = GetModeratedObjectsSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        moderatedObject = user.get_reported_object_with_id(reported_object_id=reported_object_id)

        response_serializer = GetModeratedObjectsModeratedObjectSerializer(moderatedObject,
                                                                           context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CreateModeratedObjectOutcome(APIView):
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
