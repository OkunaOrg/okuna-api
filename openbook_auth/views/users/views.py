from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.views.authenticated_user.serializers import GetAuthenticatedUserSerializer, \
    LegacyGetAuthenticatedUserSerializer
from openbook_auth.views.users.serializers import SearchUsersSerializer, SearchUsersUserSerializer, GetUserSerializer, \
    GetUserUserSerializer, GetBlockedUserSerializer, SubscribeToUserNewPostNotificationsUserSerializer, \
    GetUserPostsCountUserSerializer, LegacyGetUserUserSerializer
from openbook_common.utils.helpers import normalise_request_data
from openbook_moderation.permissions import IsNotSuspended


class SearchUsers(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 20)
        query = data.get('query')

        user = request.user

        users = user.search_users_with_query(query=query)

        users_serializer = SearchUsersUserSerializer(users[:count], many=True, context={'request': request})

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class GetUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        serializer = self._get_user_serializer_class_for_user_and_username(
            user=user, username=username
        )

        if user.username == username:
            target_user = user
        else:
            target_user = user.get_user_with_username(username=username)

        user_serializer = serializer(target_user, context={"request": request})

        return Response(user_serializer.data, status=status.HTTP_200_OK)

    def _get_user_serializer_class_for_user_and_username(self, user, username):
        if user.username == username:
            if self.request.version == '1.0':
                return GetAuthenticatedUserSerializer
            return LegacyGetAuthenticatedUserSerializer
        else:
            if self.request.version == '1.0':
                return GetUserUserSerializer
            return LegacyGetUserUserSerializer


class BlockUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        with transaction.atomic():
            blocked_user = user.block_user_with_username(username)

        user_serializer = GetBlockedUserSerializer(blocked_user, context={"request": request})

        return Response(user_serializer.data, status=status.HTTP_200_OK)


class UnblockUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        with transaction.atomic():
            unblocked_user = user.unblock_user_with_username(username)

        user_serializer = GetBlockedUserSerializer(unblocked_user, context={"request": request})

        return Response(user_serializer.data, status=status.HTTP_200_OK)


class SubscribeToUserNewPostNotifications(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request, user_username):
        request_data = normalise_request_data(request.data)
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data.get('username')
        user = request.user

        with transaction.atomic():
            user = user.enable_new_post_notifications_for_user_with_username(username=username)

        response_serializer = SubscribeToUserNewPostNotificationsUserSerializer(user, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_username):
        request_data = normalise_request_data(request.data)
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data.get('username')
        user = request.user

        with transaction.atomic():
            unsubscribed_user = user.disable_new_post_notifications_for_user_with_username(username=username)

        response_serializer = SubscribeToUserNewPostNotificationsUserSerializer(unsubscribed_user,
                                                                                context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class GetUserPostsCount(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, user_username):
        serializer = GetUserSerializer(data={'username': user_username})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        if user.username == username:
            target_user = user
        else:
            target_user = user.get_user_with_username(username=username)

        response_serializer = GetUserPostsCountUserSerializer(target_user, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
