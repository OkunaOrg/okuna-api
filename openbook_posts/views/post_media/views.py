from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_media.serializers import AddPostMediaSerializer, GetPostMediaSerializer, \
    PostMediaSerializer


class PostMedia(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request, post_uuid):
        request_data = request.data.dict()
        request_data['post_uuid'] = post_uuid

        serializer = AddPostMediaSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = request.user
        post_uuid = data.get('post_uuid')
        file = data.get('file')
        order = data.get('order')

        with transaction.atomic():
            user.add_media_to_post_with_uuid(post_uuid=post_uuid, file=file, order=order)

        return Response({
            'message': _('Media added successfully to post')
        }, status=status.HTTP_200_OK)

    def get(self, request, post_uuid):
        serializer = GetPostMediaSerializer(data={
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        post_uuid = data.get('post_uuid')

        user = request.user

        post_media = user.get_media_for_post_with_uuid(post_uuid=post_uuid).order_by(
            'order')

        post_media_serializer = PostMediaSerializer(post_media, many=True, context={"request": request})

        return Response(post_media_serializer.data, status=status.HTTP_200_OK)
