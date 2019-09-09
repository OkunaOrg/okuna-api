from django.conf import settings
from django.core.validators import FileExtensionValidator
from generic_relations.relations import GenericRelatedField
from rest_framework import serializers
from video_encoding.models import Format

from openbook_common.serializers_fields.request import RestrictedImageFileSizeField, RestrictedFileSizeField
from openbook_posts.models import PostMedia, PostImage, PostVideo
from openbook_posts.validators import post_uuid_exists, post_reaction_id_exists


class AddPostMediaSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    file = RestrictedFileSizeField(max_length=150, required=True,
                                   allow_empty_file=False, max_upload_size=settings.POST_MEDIA_MAX_SIZE)
    order = serializers.IntegerField(required=False)


class GetPostMediaSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True, required=False, allow_empty_file=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'thumbnail',
            'width',
            'height'
        )


class PostVideoFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = (
            'id',
            'duration',
            'progress',
            'format',
            'file',
            'width',
            'height',
        )


class PostVideoSerializer(serializers.ModelSerializer):
    format_set = PostVideoFormatSerializer(many=True)

    class Meta:
        model = PostVideo
        fields = (
            'file',
            'format_set',
            'width',
            'height',
            'duration',
            'thumbnail',
            'thumbnail_width',
            'thumbnail_height',
        )


class PostMediaSerializer(serializers.ModelSerializer):
    content_object = GenericRelatedField({
        PostImage: PostImageSerializer(),
        PostVideo: PostVideoSerializer(),
    })

    class Meta:
        model = PostMedia
        fields = (
            'id',
            'type',
            'content_object',
            'order'
        )
