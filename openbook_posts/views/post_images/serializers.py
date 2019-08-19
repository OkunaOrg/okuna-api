from django.conf import settings
from rest_framework import serializers

from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_posts.validators import post_uuid_exists, post_reaction_id_exists


class AddPostImageSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    image = RestrictedImageFileSizeField(allow_empty_file=False, required=False,
                                         max_upload_size=settings.POST_IMAGE_MAX_SIZE)
