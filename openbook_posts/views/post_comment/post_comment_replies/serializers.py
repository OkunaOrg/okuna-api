from rest_framework import serializers
from django.conf import settings

from openbook_common.models import Emoji
from openbook_common.serializers import CommonHashtagSerializer
from openbook_common.serializers_fields.post_comment import PostCommenterField, PostCommentReactionsEmojiCountField, \
    PostCommentReactionField, PostCommentIsMutedField
from openbook_posts.models import PostComment, PostCommentReaction
from openbook_posts.validators import post_comment_id_exists, post_uuid_exists, post_comment_text_validators

from openbook_posts.views.post_comments.serializers import PostCommentCommenterSerializer, \
    PostCommenterCommunityMembershipSerializer, PostCommentLanguageSerializer


class CommentRepliesPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH,
                                 required=True,
                                 allow_blank=False,
                                 validators=post_comment_text_validators)


class PostCommentReplyParentSerializer(serializers.ModelSerializer):
    language = PostCommentLanguageSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'language'
        )


class PostCommentReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image',
            'created',
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostCommentReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class PostCommentReactionSerializer(serializers.ModelSerializer):
    emoji = PostCommentReactionEmojiSerializer(many=False)

    class Meta:
        model = PostCommentReaction
        fields = (
            'emoji',
            'id'
        )


class PostCommentReplySerializer(serializers.ModelSerializer):
    commenter = PostCommenterField(post_commenter_serializer=PostCommentCommenterSerializer,
                                   community_membership_serializer=PostCommenterCommunityMembershipSerializer)
    parent_comment = PostCommentReplyParentSerializer()
    reactions_emoji_counts = PostCommentReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = PostCommentReactionField(post_comment_reaction_serializer=PostCommentReactionSerializer)
    is_muted = PostCommentIsMutedField()
    language = PostCommentLanguageSerializer()
    hashtags = CommonHashtagSerializer(many=True)

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'reactions_emoji_counts',
            'reaction',
            'text',
            'language',
            'created',
            'parent_comment',
            'is_edited',
            'is_muted',
            'hashtags',
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
