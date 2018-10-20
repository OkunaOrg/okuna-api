from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_posts.models import Post, PostImage
from openbook_posts.serializers import CreatePostSerializer, CreatePostPostSerializer


class CreatePost(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CreatePostSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.on_valid_request_data(serializer.validated_data, request)

    def on_valid_request_data(self, data, request):
        text = data.get('text')
        image = data.get('image')
        user = request.user

        with transaction.atomic():
            post = Post.objects.create(text=text, creator=user)
            if image:
                PostImage.objects.create(image=image, post=post)

        post_serializer = CreatePostPostSerializer(post, context={"request": request})

        return Response(post_serializer.data, status=status.HTTP_201_CREATED)
