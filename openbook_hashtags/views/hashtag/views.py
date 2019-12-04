# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.serializers import CommonHashtagSerializer
from openbook_hashtags.views.hashtag.serializers import GetHashtagSerializer, \
    GetHashtagPostsSerializer, GetHashtagPostsPostSerializer, GetHashtagHashtagSerializer
from openbook_moderation.permissions import IsNotSuspended


class HashtagItem(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, hashtag_name):
        request_data = request.data.copy()
        request_data['hashtag_name'] = hashtag_name

        serializer = GetHashtagSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        hashtag_name = data.get('hashtag_name')

        user = request.user

        hashtag = user.get_hashtag_with_name(hashtag_name=hashtag_name)

        hashtag_serializer = GetHashtagHashtagSerializer(hashtag, context={'request': request})

        return Response(hashtag_serializer.data, status=status.HTTP_200_OK)


class HashtagPosts(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def get(self, request, hashtag_name):
        query_params = request.query_params.dict()
        query_params['hashtag_name'] = hashtag_name

        serializer = GetHashtagPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        hashtag_name = data.get('hashtag_name')
        count = data.get('count')
        max_id = data.get('max_id')

        user = request.user

        hashtag_posts = user.get_posts_for_hashtag_with_name(hashtag_name=hashtag_name, max_id=max_id).order_by('-id')[
                        :count]

        hashtag_posts_serializer = GetHashtagPostsPostSerializer(hashtag_posts, context={'request': request}, many=True)

        return Response(hashtag_posts_serializer.data, status=status.HTTP_200_OK)
