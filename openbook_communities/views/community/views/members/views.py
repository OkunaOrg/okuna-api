# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _

from openbook_common.responses import ApiMessageResponse
from openbook_common.utils.helpers import normalise_request_data
from openbook_communities.views.community.views.members.serializers import AddCommunityMemberSerializer, \
    GetCommunityMembersSerializer, GetCommunityMembersMemberSerializer, RemoveCommunityMemberSerializer


class CommunityMembers(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = AddCommunityMemberSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        username = data.get('username')

        user = request.user

        with transaction.atomic():
            user.add_community_member_with_username_to_community_with_name(member_username=username,
                                                                           community_name=community_name)

        return ApiMessageResponse(_('Member added.'), status=status.HTTP_201_CREATED)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityMembersSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        query = data.get('query')

        user = request.user

        members = user.get_community_with_name_members_with_query(community_name=community_name, query=query)[:count]

        response_serializer = GetCommunityMembersMemberSerializer(members, many=True,
                                                                  context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CommunityMember(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, community_name, member_username):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name
        request_data['member_username'] = member_username

        serializer = RemoveCommunityMemberSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.remove_community_member_with_username_from_community_with_name(member_username=member_username,
                                                                                community_name=community_name)

        return Response(status=status.HTTP_200_OK)
