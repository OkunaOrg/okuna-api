from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_auth.views.authenticated_user.serializers import GetAuthenticatedUserSerializer
from openbook_auth.views.users.serializers import SearchUsersSerializer, SearchUsersUserSerializer, GetUserSerializer, \
    GetUserUserSerializer
from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.model_loaders import get_user_model
from django.utils.translation import ugettext_lazy as _


class SearchUsers(APIView):
    def get(self, request):
        query_params = request.query_params.dict()
        serializer = SearchUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 20)
        query = data.get('query')

        user = request.user

        if user.is_anonymous:
            User = get_user_model()
            users = User.get_public_users_with_query(query=query)
        else:
            users = user.search_users_with_query(query=query)

        users_serializer = SearchUsersUserSerializer(users[:count], many=True, context={'request': request})

        return Response(users_serializer.data, status=status.HTTP_200_OK)


class GetUser(APIView):
    def get(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        User = get_user_model()

        user = User.get_user_with_username(username)

        user_serializer = None

        if not request.user.is_anonymous:
            authenticated_user = request.user
            if authenticated_user.username == user_username:
                user_serializer = GetAuthenticatedUserSerializer(user, context={"request": request})

        if not user_serializer:
            user_serializer = GetUserUserSerializer(user, context={"request": request})

        return Response(user_serializer.data, status=status.HTTP_200_OK)


class BlockUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.block_user_with_username(username)

        return ApiMessageResponse(_('Blocked account.'))


class UnblockUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_username):
        request_data = request.data.copy()
        request_data['username'] = user_username

        serializer = GetUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.unblock_user_with_username(username)

        return ApiMessageResponse(_('Unblocked account.'))
