from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_posts.models import PostComment
from openbook_posts.validators import post_id_exists, post_comment_id_exists


class DeletePostSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )


class PostCommenterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
        )


class PostCommentCommenterSerializer(serializers.ModelSerializer):
    profile = PostCommenterProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'profile',
        )


class PostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommentCommenterSerializer(many=False)

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'text',
            'created',
            'id'
        )


class CommentPostSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class GetPostCommentsSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    min_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class DeletePostCommentSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
