from django.conf import settings
from django.core.validators import FileExtensionValidator
from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_posts.models import PostMedia, PostImage, PostVideo
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
            'width',
            'height'
        )


class PostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = (
            'file',
            'format_set',
            'width',
            'height',
            'duration'
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
            'position'
        )
