from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_image.serializers import SetPostImageSerializer


class PostImage(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)

    def put(self, request, post_uuid):
        request_data = request.data.dict()
        request_data['post_uuid'] = post_uuid

        serializer = SetPostImageSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = request.user
        post_uuid = data.get('post_uuid')
        image = data.get('image')

        with transaction.atomic():
            user.add_image_to_post_with_uuid(post_uuid=post_uuid, image=image)

        return Response({
            'message': _('Image set successfully to post')
        }, status=status.HTTP_200_OK)
