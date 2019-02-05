from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.helpers import normalise_request_data
from openbook_communities.views.community.serializers import GetCommunityCommunitySerializer, DeleteCommunitySerializer, \
    UpdateCommunitySerializer, UpdateCommunityAvatarSerializer, UpdateCommunityCoverSerializer, GetCommunitySerializer


class CommunityItem(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        serializer = GetCommunitySerializer(data={'community_name': community_name})
        serializer.is_valid(raise_exception=True)

        user = request.user
        community = user.get_community_with_name(community_name)

        response_serializer = GetCommunityCommunitySerializer(community, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, community_name):
        serializer = DeleteCommunitySerializer(data={'community_name': community_name})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_community_with_name(community_name)

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = UpdateCommunitySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        name = data.get('name')
        type = data.get('type')
        title = data.get('title')
        description = data.get('description')
        rules = data.get('rules')
        user_adjective = data.get('user_adjective')
        users_adjective = data.get('users_adjective')

        user = request.user

        with transaction.atomic():
            community = user.update_community_with_name(community_name, name=name, type=type, title=title,
                                                        description=description,
                                                        rules=rules, user_adjective=user_adjective,
                                                        users_adjective=users_adjective)

        response_serializer = GetCommunityCommunitySerializer(community, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CommunityAvatar(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = UpdateCommunityAvatarSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        data = serializer.validated_data
        avatar = data.get('avatar')

        with transaction.atomic():
            user.update_community_with_name_avatar(community_name, avatar=avatar)

        return Response(status=status.HTTP_200_OK)

    def delete(self, request, community_name):
        user = request.user

        with transaction.atomic():
            user.delete_community_with_name_avatar(community_name)

        return Response(status=status.HTTP_200_OK)


class CommunityCover(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = UpdateCommunityCoverSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        data = serializer.validated_data
        cover = data.get('cover')

        with transaction.atomic():
            user.update_community_with_name_cover(community_name, cover=cover)

        return Response(status=status.HTTP_200_OK)

    def delete(self, request, community_name):
        user = request.user

        with transaction.atomic():
            user.delete_community_with_name_cover(community_name)

        return Response(status=status.HTTP_200_OK)
