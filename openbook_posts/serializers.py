from rest_framework import serializers

from openbook.settings import POST_MAX_LENGTH, COMMENT_MAX_LENGTH
from openbook_posts.models import PostImage, Post


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=POST_MAX_LENGTH, required=True, allow_blank=False)
    image = serializers.ImageField(allow_empty_file=True, required=False)


class CommentPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class ReactToPostSerializer(serializers.Serializer):
    reaction_id = serializers.IntegerField(required=True, min_value=0)


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = PostImage
        fields = (
            'image',
        )


class PostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)

    class Meta:
        model = Post
        fields = (
            'id',
            'created',
            'text',
            'image'
        )
