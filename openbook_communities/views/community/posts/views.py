# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_communities.views.community.posts.serializers import GetCommunityPostsSerializer, CommunityPostSerializer


class CommunityPosts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, community_name):
        query_params = request.query_params.dict()
        query_params['community_name'] = community_name

        serializer = GetCommunityPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        posts = user.get_posts_for_community_with_name(community_name=community_name, max_id=max_id).order_by('-created')[:count]

        response_serializer = CommunityPostSerializer(posts, many=True,
                                                      context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)
