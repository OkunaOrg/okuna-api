from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_posts.models import Post, PostImage
from openbook_posts.serializers import CreatePostSerializer, PostSerializer


class Posts(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def put(self, request):
        serializer = CreatePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        text = data.get('text')
        image = data.get('image')
        user = request.user

        with transaction.atomic():
            post = Post.objects.create(text=text, creator=user)
            if image:
                PostImage.objects.create(image=image, post=post)

        post_serializer = PostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        post_serializer = PostSerializer(user.posts, many=True, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_200_OK)
