# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_connections.serializers import ConnectWithUserSerializer, ConnectionSerializer, \
    DisconnectFromUserSerializer, UpdateConnectionSerializer, ConfirmConnectionSerializer


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
        user_id = data.get('user_id')
        circle_id = data.get('circle_id')

        user = request.user

        with transaction.atomic():
            connection = user.connect_with_user_with_id(user_id, circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DisconnectFromUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DisconnectFromUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_id = data.get('user_id')

        user = request.user

        with transaction.atomic():
            user.disconnect_from_user_with_id(user_id)

        return Response(status=status.HTTP_200_OK)


class UpdateConnection(APIView):
    def post(self, request):
        serializer = UpdateConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user_id = data.get('user_id')
        circle_id = data.get('circle_id')
        user = request.user

        with transaction.atomic():
            connection = user.update_connection_with_user_with_id(user_id, circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConfirmConnection(APIView):
    def post(self, request):
        serializer = ConfirmConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user_id = data.get('user_id')
        circle_id = data.get('circle_id')
        user = request.user

        with transaction.atomic():
            connection = user.confirm_connection_with_user_with_id(user_id, circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
