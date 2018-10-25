from rest_framework import serializers

from openbook.settings import POST_MAX_LENGTH, COMMENT_MAX_LENGTH
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_lists.validators import list_with_id_exists_for_user_with_id
from openbook_posts.models import PostImage, Post


class GetPostsSerializer(serializers.Serializer):
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField()
    )
    list_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField()
    )

    def validate_circle_id(self, circle_id):
        user = self.context.get("request").user
        if circle_id:
            for id in circle_id:
                circle_id_exists(id, user.pk)
        return circle_id

    def validate_list_id(self, list_id):
        user = self.context.get("request").user
        if list_id:
            for id in list_id:
                list_with_id_exists_for_user_with_id(id, user.pk)
        return list_id


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=POST_MAX_LENGTH, required=True, allow_blank=False)
    image = serializers.ImageField(allow_empty_file=True, required=False)
    circle_id = serializers.ListField(
        child=serializers.IntegerField()
    )

    def validate_circle_id(self, circle_id):
        request = self.context.get("request")
        user = request.user
        if circle_id:
            for id in circle_id:
                circle_id_exists(id, user.pk)
        return circle_id


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


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name'
        )


class PostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)

    class Meta:
        model = Post
        fields = (
            'id',
            'created',
            'text',
            'image',
            'creator_id'
        )
