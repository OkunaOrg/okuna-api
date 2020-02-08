# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.helpers import normalize_list_value_in_request_data
from openbook_moderation.permissions import IsNotSuspended
from openbook_notifications.serializers import GetNotificationsSerializer, GetNotificationsNotificationSerializer, \
    DeleteNotificationSerializer, ReadNotificationSerializer, ReadNotificationsSerializer, \
    UnreadNotificationsCountSerializer


class Notifications(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        query_params = request.query_params.dict()

        normalize_list_value_in_request_data('types', query_params)

        serializer = GetNotificationsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        types = data.get('types')

        notifications = user.get_notifications(max_id=max_id, types=types).order_by('-created')[:count]

        response_serializer = GetNotificationsNotificationSerializer(notifications, many=True,
                                                                     context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user

        with transaction.atomic():
            user.delete_own_notifications()

        return Response(status=status.HTTP_200_OK)


class ReadNotifications(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        query_data = request.data.dict()

        if 'types' in query_data:
            query_data['types'] = query_data['types'].split(sep=",")

        serializer = ReadNotificationsSerializer(data=query_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        max_id = data.get('max_id')
        types = data.get('types')

        with transaction.atomic():
            user.read_notifications(max_id=max_id, types=types)

        return Response(status=status.HTTP_200_OK)


class UnreadNotificationsCount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        query_params = request.query_params.dict()

        normalize_list_value_in_request_data('types', query_params)

        serializer = UnreadNotificationsCountSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        max_id = data.get('max_id')
        types = data.get('types')

        notifications = user.get_unread_notifications(max_id=max_id, types=types)

        return Response({'count': notifications.count()}, status=status.HTTP_200_OK)


class NotificationItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def delete(self, request, notification_id):
        serializer = DeleteNotificationSerializer(data={'notification_id': notification_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_notification_with_id(notification_id)

        return Response(status=status.HTTP_200_OK)


class ReadNotification(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, notification_id):
        serializer = ReadNotificationSerializer(data={'notification_id': notification_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.read_notification_with_id(notification_id)

        return Response(status=status.HTTP_200_OK)
