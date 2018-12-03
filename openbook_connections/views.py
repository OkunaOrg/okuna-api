# Create your views here.
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_connections.serializers import ConnectWithUserSerializer, ConnectionSerializer, \
    DisconnectFromUserSerializer, UpdateConnectionSerializer, ConfirmConnectionSerializer, ConnectionUserSerializer


class Connections(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_serializer = ConnectionSerializer(user.connections, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConnectWithUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ConnectWithUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')
        circle_id = data.get('circle_id')

        user = request.user

        User = get_user_model()
        user_to_connect_with = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.connect_with_user_with_id(user_to_connect_with.pk, circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DisconnectFromUser(APIView):
    permission_classes = (IsAuthenticated,)

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
    def post(self, request):
        serializer = UpdateConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        username = data.get('username')
        circle_id = data.get('circle_id')

        user = request.user

        User = get_user_model()
        user_to_update_connection_from = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.update_connection_with_user_with_id(user_to_update_connection_from.pk,
                                                                  circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConfirmConnection(APIView):
    def post(self, request):
        serializer = ConfirmConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        username = data.get('username')
        circle_id = data.get('circle_id')

        user = request.user

        User = get_user_model()
        user_to_confirm_connection_with = User.objects.get(username=username)

        with transaction.atomic():
            connection = user.confirm_connection_with_user_with_id(user_to_confirm_connection_with.pk,
                                                                   circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
