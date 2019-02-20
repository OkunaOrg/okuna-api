# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import normalise_request_data
from openbook_communities.views.community.members.serializers import JoinCommunitySerializer, \
    GetCommunityMembersSerializer, GetCommunityMembersMemberSerializer, LeaveCommunitySerializer, \
    InviteCommunityMemberSerializer, MembersCommunitySerializer, SearchCommunityMembersSerializer


class CommunityMembers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityMembersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        members = user.get_community_with_name_members(community_name=community_name, max_id=max_id)[:count]

        response_serializer = GetCommunityMembersMemberSerializer(members, many=True,
                                                                  context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class JoinCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = JoinCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            community = user.join_community_with_name(community_name=community_name)

        return Response(MembersCommunitySerializer(community, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class LeaveCommunity(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = LeaveCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            community = user.leave_community_with_name(
                community_name=community_name)

        return Response(MembersCommunitySerializer(community, context={'request': request}).data,
                        status=status.HTTP_200_OK, )


class InviteCommunityMember(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = InviteCommunityMemberSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.invite_user_with_username_to_community_with_name(username=username,
                                                                  community_name=community_name)

        return ApiMessageResponse(_('Invited user successfully!'), status=status.HTTP_201_CREATED)


class SearchCommunityMembers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = SearchCommunityMembersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        members = user.search_community_with_name_members(community_name=community_name, query=query)[
                  :count]

        response_serializer = GetCommunityMembersMemberSerializer(members, many=True,
                                                                  context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
