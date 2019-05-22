# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import normalise_request_data
from openbook_communities.views.community.banned_users.serializers import GetCommunityBannedUsersUserSerializer, \
    GetCommunityBannedUsersSerializer, BanUserSerializer, UnbanUserSerializer, SearchCommunityBannedUsersSerializer


class CommunityBannedUsers(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityBannedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        banned_users = user.get_community_with_name_banned_users(community_name=community_name, max_id=max_id).order_by(
            '-id')[:count]

        response_serializer = GetCommunityBannedUsersUserSerializer(banned_users, many=True,
                                                                    context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class BanUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = BanUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.ban_user_with_username_from_community_with_name(username=username, community_name=community_name)

        return ApiMessageResponse(_('Banned user!'), status=status.HTTP_200_OK)


class UnbanUser(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = UnbanUserSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.unban_user_with_username_from_community_with_name(username=username, community_name=community_name)

        return ApiMessageResponse(_('Unbanned user!'), status=status.HTTP_200_OK)


class SearchCommunityBannedUsers(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = SearchCommunityBannedUsersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        banned_users = user.search_community_with_name_banned_users(community_name=community_name, query=query)[
                       :count]

        response_serializer = GetCommunityBannedUsersUserSerializer(banned_users, many=True,
                                                                    context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
