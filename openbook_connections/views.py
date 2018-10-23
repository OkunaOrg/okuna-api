# Create your views here.
from django.apps import apps
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_connections.models import Connection
from openbook_connections.serializers import CreateConnectionSerializer, ConnectionSerializer, \
    DeleteConnectionSerializer


class Connections(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = CreateConnectionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_id = data.get('user_id')
        circle_id = data.get('circle_id')

        user = request.user

        with transaction.atomic():
            connection = Connection.create_connection(user_id=user.pk, target_user_id=user_id, circle_id=circle_id)

        response_serializer = ConnectionSerializer(connection, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        response_serializer = ConnectionSerializer(user.connections, many=True, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConnectionItem(APIView):
    def delete(self, request, connection_id):
        user = request.user
        serializer = DeleteConnectionSerializer(data={'connection_id': connection_id}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        connection = user.connections.get(id=connection_id)
        with transaction.atomic():
            connection.delete()
        return Response(status=status.HTTP_200_OK)
