# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data, normalize_list_value_in_request_data
from openbook_communities.views.community.members.serializers import JoinCommunitySerializer, \
    GetCommunityMembersSerializer, GetCommunityMembersMemberSerializer, LeaveCommunitySerializer, \
    InviteCommunityMemberSerializer, MembersCommunitySerializer, SearchCommunityMembersSerializer, InviteUserSerializer


class CommunityMembers(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        normalize_list_value_in_request_data(request_data=query_params, list_name='exclude')
        query_params['community_name'] = community_name

        serializer = GetCommunityMembersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')
        exclude = data.get('exclude')

        user = request.user

        members = user.get_community_with_name_members(community_name=community_name, max_id=max_id,
                                                       exclude_keywords=exclude).order_by(
            '-id')[:count]

        response_serializer = GetCommunityMembersMemberSerializer(members, many=True,
                                                                  context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class JoinCommunity(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

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
    permission_classes = (IsAuthenticated, IsNotSuspended)

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
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = InviteCommunityMemberSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            community_invite = user.invite_user_with_username_to_community_with_name(username=username,
                                                                                     community_name=community_name)

        response_serializer = InviteUserSerializer(community_invite.invited_user,
                                                   context={"request": request, 'communities_names': [community_name]})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UninviteCommunityMember(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def post(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = InviteCommunityMemberSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        username = data.get('username')

        user = request.user

        with transaction.atomic():
            uninvited_user = user.uninvite_user_with_username_to_community_with_name(username=username,
                                                                                     community_name=community_name)

        response_serializer = InviteUserSerializer(uninvited_user,
                                                   context={"request": request, 'communities_names': [community_name]})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class SearchCommunityMembers(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name
        normalize_list_value_in_request_data(request_data=query_params, list_name='exclude')

        serializer = SearchCommunityMembersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')
        exclude = data.get('exclude')

        user = request.user

        members = user.search_community_with_name_members(community_name=community_name, query=query,
                                                          exclude_keywords=exclude)[
                  :count]

        response_serializer = GetCommunityMembersMemberSerializer(members, many=True,
                                                                  context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
