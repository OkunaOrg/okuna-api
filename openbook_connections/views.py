# Create your views here.
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_connections.serializers import ConnectWithUserSerializer, ConnectionSerializer, \
    DisconnectFromUserSerializer, UpdateConnectionSerializer, ConfirmConnectionSerializer, ConnectionUserSerializer


class Connections(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_serializer = ConnectionSerializer(user.connections, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConnectWithUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        request_data = _prepare_request_data_for_validation(request.data)

        serializer = ConnectWithUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')
        circles_ids = data.get('circles_ids')

        user = request.user

        User = get_user_model()
        user_to_connect_with = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.connect_with_user_with_id(user_to_connect_with.pk, circles_ids=circles_ids)

        response_serializer = ConnectionSerializer(connection, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DisconnectFromUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        serializer = DisconnectFromUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        User = get_user_model()
        user_to_disconnect_from = User.objects.get(username=username)

        with transaction.atomic():
            user.disconnect_from_user_with_id(user_to_disconnect_from.pk)

        response_serializer = ConnectionUserSerializer(user_to_disconnect_from, context={'request': request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UpdateConnection(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        request_data = _prepare_request_data_for_validation(request.data)

        serializer = UpdateConnectionSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        username = data.get('username')
        circles_ids = data.get('circles_ids')

        user = request.user

        User = get_user_model()
        user_to_update_connection_from = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.update_connection_with_user_with_id(user_to_update_connection_from.pk,
                                                                  circles_ids=circles_ids)

        response_serializer = ConnectionSerializer(connection, context={'request': request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConfirmConnection(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request):
        request_data = _prepare_request_data_for_validation(request.data)

        serializer = ConfirmConnectionSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        username = data.get('username')
        circles_ids = data.get('circles_ids')

        user = request.user

        User = get_user_model()
        user_to_confirm_connection_with = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.confirm_connection_with_user_with_id(user_to_confirm_connection_with.pk,
                                                                   circles_ids=circles_ids)

        response_serializer = ConnectionSerializer(connection, context={'request': request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


def _prepare_request_data_for_validation(request_data):
    request_data_copy = normalise_request_data(request_data)
    circles_ids = request_data_copy.get('circles_ids', None)
    if isinstance(circles_ids, str):
        circles_ids = circles_ids.split(',')
        request_data_copy['circles_ids'] = circles_ids
    return request_data_copy
