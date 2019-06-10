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
from openbook_communities.views.community.administrators.serializers import GetCommunityAdministratorsSerializer, \
    GetCommunityAdministratorsUserSerializer, RemoveCommunityAdministratorSerializer, \
    AddCommunityAdministratorSerializer, SearchCommunityAdministratorsSerializer


class CommunityAdministrators(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityAdministratorsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        administrators = user.get_community_with_name_administrators(community_name=community_name,
                                                                     max_id=max_id).order_by(
            '-id')[
                         :count]

        response_serializer = GetCommunityAdministratorsUserSerializer(administrators, many=True,
                                                                       context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = AddCommunityAdministratorSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')
        user = request.user

        with transaction.atomic():
            user.add_administrator_with_username_to_community_with_name(username=username,
                                                                        community_name=community_name)

        return ApiMessageResponse('Added administrator to community.', status=status.HTTP_201_CREATED)


class CommunityAdministratorItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def delete(self, request, community_name, community_administrator_username):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name
        request_data['username'] = community_administrator_username

        serializer = RemoveCommunityAdministratorSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.remove_administrator_with_username_from_community_with_name(username=username,
                                                                             community_name=community_name)

        return ApiMessageResponse(_('Removed administrator'), status=status.HTTP_200_OK)


class SearchCommunityAdministrators(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = SearchCommunityAdministratorsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        administrators = user.search_community_with_name_administrators(community_name=community_name, query=query)[
                         :count]

        response_serializer = GetCommunityAdministratorsUserSerializer(administrators, many=True,
                                                                       context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
