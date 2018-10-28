from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_posts.models import Post
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
            post = user.create_post(text=text, circles_ids=circles_ids, image=image)
            # post = Post.create_post(text=text, creator=user, circles_ids=circles_ids, image=image)

        post_serializer = PostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        query_params = {**request.query_params}

        # TODO There must be a better way to validate query params :facepalm:

        count = query_params.get('count', None)
        if count:
            query_params['count'] = int(count[0])

        max_id = query_params.get('max_id', None)
        if max_id:
            query_params['max_id'] = int(max_id[0])

        circle_id = query_params.get('circle_id', None)
        if circle_id:
            query_params['circle_id'] = query_params['circle_id'][0].split(',')

        list_id = query_params.get('list_id', None)
        if list_id:
            query_params['list_id'] = query_params['list_id'][0].split(',')

        serializer = GetPostsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        circles_ids = data.get('circle_id')
        lists_ids = data.get('list_id')
        max_id = data.get('max_id')
        count = data.get('count', 10)

        user = request.user

        posts = user.get_posts(
            circles_ids=circles_ids,
            lists_ids=lists_ids,
            max_id=max_id
        ).order_by('-created')[:count]

        post_serializer = PostSerializer(posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)
