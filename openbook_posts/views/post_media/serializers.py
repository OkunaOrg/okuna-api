from django.conf import settings
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_posts.validators import post_uuid_exists, post_reaction_id_exists


class AddPostMediaSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    file = serializers.FileField(max_length=20, required=True,
                                 allow_empty_file=False,
                                 validators=[
                                     FileExtensionValidator(
                                         allowed_extensions=['mp4', '.3gp', 'gif', 'jpg', 'jpeg', 'png'])])
    position = serializers.IntegerField()
