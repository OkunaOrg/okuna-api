from rest_framework import serializers
from django.conf import settings
from openbook_common.serializers_fields.post_comment import PostCommenterField
from openbook_posts.models import PostComment
from openbook_posts.validators import post_comment_id_exists, post_uuid_exists

from openbook_posts.views.post_comments.serializers import PostCommentCommenterSerializer, \
    PostCommenterCommunityMembershipSerializer


class EditPostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'is_edited'
        )


class DeletePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )


class UpdatePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class CommentRepliesPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class PostCommentReplyParentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostComment
        fields = (
            'id',
        )


class PostCommentReplySerializer(serializers.ModelSerializer):
    commenter = PostCommenterField(post_commenter_serializer=PostCommentCommenterSerializer,
                                   community_membership_serializer=PostCommenterCommunityMembershipSerializer)
    parent_comment = PostCommentReplyParentSerializer()

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'text',
            'created',
            'parent_comment',
            'is_edited',
            'id'
        )


class GetPostCommentRepliesSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    min_id = serializers.IntegerField(
        required=False,
    )
    count_max = serializers.IntegerField(
        required=False,
        max_value=20
    )
    count_min = serializers.IntegerField(
        required=False,
        max_value=20
    )
    sort = serializers.ChoiceField(required=False, choices=[
        'ASC',
        'DESC'
    ])
