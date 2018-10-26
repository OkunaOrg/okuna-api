from rest_framework import serializers

from openbook.settings import POST_MAX_LENGTH, COMMENT_MAX_LENGTH
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_lists.validators import list_id_exists
from openbook_posts.models import PostImage, Post


class GetPostsSerializer(serializers.Serializer):
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )
    list_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[list_id_exists])
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=POST_MAX_LENGTH, required=True, allow_blank=False)
    image = serializers.ImageField(allow_empty_file=True, required=False)
    circle_id = serializers.ListField(
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )


class CommentPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class ReactToPostSerializer(serializers.Serializer):
    reaction_id = serializers.IntegerField(required=True, min_value=0)


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name'
        )


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'created',
            'text',
            'creator_id'
        )
