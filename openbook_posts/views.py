from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_posts.models import Post, PostImage
from openbook_posts.serializers import CreatePostSerializer, PostSerializer, GetPostsSerializer


class Posts(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def put(self, request):
        serializer = CreatePostSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        text = data.get('text')
        image = data.get('image')
        circles_ids = data.get('circle_id')
        user = request.user

        with transaction.atomic():
            post = Post.create_post(text=text, creator=user, circles_ids=circles_ids, image=image)

        post_serializer = PostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user

        serializer = GetPostsSerializer(data=request.query_params, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        circles_ids = data.get('circle_id')
        lists_ids = data.get('list_id')

        posts = Post.get_posts_for_user(
            user,
            circles_ids=circles_ids,
            lists_ids=lists_ids
        ).order_by('-created')[:10]

        post_serializer = PostSerializer(posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)


class PostView(APIView):
    def get(self, request, post_id):
        user = request.user
        try:
            post = user.posts.get(pk=post_id)
        except Post.DoesNotExist:
            raise NotFound()

        post_serializer = PostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)


class PostComments(APIView):
    def get(self, request, post_id):
        pass

    def put(self, request, post_id):
        pass


class PostReactions(APIView):
    def get(self, request, post_id):
        pass

    def put(self, request, post_id):
        pass
