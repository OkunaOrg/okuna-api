from django.db import transaction
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import ugettext_lazy as _

from openbook_moderation.permissions import IsNotSuspended
from openbook_posts.views.post_images.serializers import AddPostImageSerializer


class AddPostImage(APIView):
    permission_classes = (IsAuthenticated, IsNotSuspended)
    parser_classes = [FileUploadParser]

    def put(self, request, post_uuid):
        serializer = AddPostImageSerializer(data={
            'image': request.data['file'],
            'post_uuid': post_uuid
        })
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = request.user
        post_uuid = data.get('post_uuid')
        image = data.get('image')

        with transaction.atomic():
            user.add_image_to_post_with_uuid(post_uuid=post_uuid, image=image)

        return Response({
            'message': _('Image added successfully to post')
        }, status=status.HTTP_200_OK)
