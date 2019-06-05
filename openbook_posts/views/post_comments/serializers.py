from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_common.serializers_fields.post_comment import PostCommenterField, RepliesCountField
from openbook_communities.models import CommunityMembership
from openbook_posts.models import PostComment, Post
from openbook_posts.validators import post_uuid_exists
from openbook_posts.views.post_comments.serializer_fields import RepliesField


class PostCommenterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'name'
        )


class PostCommentCommenterSerializer(serializers.ModelSerializer):
    profile = PostCommenterProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'username',
            'profile',
            'id'
        )


class PostCommenterCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class PostCommentRepliesParentCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = (
            'id',
        )


class PostCommentReplySerializer(serializers.ModelSerializer):
    parent_comment = PostCommentRepliesParentCommentSerializer()
    commenter = PostCommenterField(post_commenter_serializer=PostCommentCommenterSerializer,
                                   community_membership_serializer=PostCommenterCommunityMembershipSerializer)

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'parent_comment',
            'text',
            'created',
            'is_edited',
            'id'
        )


class PostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommenterField(post_commenter_serializer=PostCommentCommenterSerializer,
                                   community_membership_serializer=PostCommenterCommunityMembershipSerializer)
    replies = RepliesField(post_comment_reply_serializer=PostCommentReplySerializer)
    replies_count = RepliesCountField()

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'text',
            'created',
            'replies_count',
            'replies',
            'is_edited',
            'id'
        )


class CommentPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class GetPostCommentsSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
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


class EnableDisableCommentsPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'comments_enabled'
        )


class DisableCommentsPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class EnableCommentsPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
