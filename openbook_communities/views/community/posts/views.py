# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from openbook_moderation.permissions import IsNotSuspended
from openbook_common.utils.helpers import normalise_request_data
from openbook_communities.views.community.posts.serializers import GetCommunityPostsSerializer, CommunityPostSerializer, \
    CreateCommunityPostSerializer, GetCommunityPostsCountsSerializer, GetCommunityPostsCountCommunitySerializer


class CommunityPosts(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        posts = user.get_posts_for_community_with_name(community_name=community_name, max_id=max_id).order_by(
            '-created')[:count]

        response_serializer = CommunityPostSerializer(posts, many=True,
                                                      context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, community_name):
        request_data = normalise_request_data(request.data)
        request_data['community_name'] = community_name

        serializer = CreateCommunityPostSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        text = data.get('text')
        image = data.get('image')
        video = data.get('video')
        community_name = data.get('community_name')
        is_draft = data.get('is_draft')

        user = request.user

        with transaction.atomic():
            post = user.create_community_post(text=text, community_name=community_name, image=image, video=video,
                                              is_draft=is_draft)

        post_serializer = CommunityPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)


class ClosedCommunityPosts(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        posts = user.get_closed_posts_for_community_with_name(community_name=community_name, max_id=max_id).order_by(
            '-created')[:count]

        response_serializer = CommunityPostSerializer(posts, many=True,
                                                      context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class GetCommunityPostsCount(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, community_name):
        serializer = GetCommunityPostsCountsSerializer(data={'community_name': community_name})
        serializer.is_valid(raise_exception=True)

        user = request.user
        community = user.get_community_with_name(community_name)

        response_serializer = GetCommunityPostsCountCommunitySerializer(community, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
