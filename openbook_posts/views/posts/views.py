from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.permissions import IsGetOrIsAuthenticated
from openbook_posts.views.posts.serializers import CreatePostSerializer, AuthenticatedUserPostSerializer, \
    GetPostsSerializer, UnauthenticatedUserPostSerializer


class Posts(APIView):
    permission_classes = (IsGetOrIsAuthenticated,)

    def put(self, request):

        request_data = request.data.dict()

        circle_id = request_data.get('circle_id', None)
        if circle_id and isinstance(circle_id, str):
            circle_id = circle_id.split(',')
            request_data['circle_id'] = circle_id

        serializer = CreatePostSerializer(data=request_data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        text = data.get('text')
        image = data.get('image')
        circles_ids = data.get('circle_id')
        user = request.user

        with transaction.atomic():
            post = user.create_post(text=text, circles_ids=circles_ids, image=image)

        post_serializer = AuthenticatedUserPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):

        if request.user.is_authenticated:
            return self.get_posts_for_authenticated_user(request)
        return self.get_posts_for_unauthenticated_user(request)

    def get_posts_for_authenticated_user(self, request):
        query_params = request.query_params.dict()

        circle_id = query_params.get('circle_id', None)
        if circle_id:
            query_params['circle_id'] = query_params['circle_id'].split(',')

        list_id = query_params.get('list_id', None)
        if list_id:
            query_params['list_id'] = query_params['list_id'].split(',')

        serializer = GetPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        circles_ids = data.get('circle_id')
        lists_ids = data.get('list_id')
        max_id = data.get('max_id')
        count = data.get('count', 10)
        username = data.get('username')

        user = request.user

        posts = user.get_timeline_posts(
            circles_ids=circles_ids,
            lists_ids=lists_ids,
            max_id=max_id,
            username=username
        ).order_by('-created')[:count]

        post_serializer = AuthenticatedUserPostSerializer(posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)

    def get_posts_for_unauthenticated_user(self, request):
        query_params = request.query_params.dict()

        serializer = GetPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        max_id = data.get('max_id')
        count = data.get('count', 10)
        username = data.get('username')

        User = get_user_model()

        posts = User.get_public_posts_for_user_with_username(
            max_id=max_id,
            username=username
        ).order_by('-created')[:count]

        post_serializer = UnauthenticatedUserPostSerializer(posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)


class TrendingPosts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        Post = get_post_model()
        posts = Post.get_trending_posts()[:5]
        posts_serializer = AuthenticatedUserPostSerializer(posts, many=True, context={"request": request})
        return Response(posts_serializer.data, status=status.HTTP_200_OK)
