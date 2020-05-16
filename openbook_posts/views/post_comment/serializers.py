from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_common.models import Language, Emoji
from openbook_common.serializers import CommonUserProfileBadgeSerializer, CommonHashtagSerializer, \
    CommonPublicUserSerializer
from openbook_common.serializers_fields.post_comment import PostCommenterField, PostCommentReactionsEmojiCountField, \
    PostCommentReactionField, PostCommentIsMutedField, RepliesCountField
from openbook_communities.models import CommunityMembership
from openbook_posts.models import PostComment, PostCommentReaction
from openbook_posts.validators import post_comment_id_exists, post_uuid_exists, \
    post_comment_id_exists_for_post_with_uuid
from openbook_posts.views.posts.serializers import PostLanguageSerializer


class EditPostCommentSerializer(serializers.ModelSerializer):
    language = PostLanguageSerializer()
    hashtags = CommonHashtagSerializer(many=True)

    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'language',
            'is_edited',
            'hashtags'
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


class GetPostCommentRequestSerializer(serializers.Serializer):
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


class MutePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )

    def validate(self, data):
        post_comment_id_exists_for_post_with_uuid(post_comment_id=data['post_comment_id'], post_uuid=data['post_uuid'])
        return data


class UnmutePostCommentSerializer(MutePostCommentSerializer):
    pass


class TranslatePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )


class GetPostCommenterCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class PostCommentLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
        )


class PostCommentRepliesParentCommentSerializer(serializers.ModelSerializer):
    language = PostCommentLanguageSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'language',
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


class GetPostCommentReactionEmojiCountSerializer(serializers.Serializer):
    emoji = PostCommentReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class GetPostCommentReactionSerializer(serializers.ModelSerializer):
    emoji = PostCommentReactionEmojiSerializer(many=False)

    class Meta:
        model = PostCommentReaction
        fields = (
            'emoji',
            'id'
        )


class GetPostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommenterField(post_commenter_serializer=CommonPublicUserSerializer,
                                   community_membership_serializer=GetPostCommenterCommunityMembershipSerializer)
    replies_count = RepliesCountField()
    reactions_emoji_counts = PostCommentReactionsEmojiCountField(
        emoji_count_serializer=GetPostCommentReactionEmojiCountSerializer)
    reaction = PostCommentReactionField(post_comment_reaction_serializer=GetPostCommentReactionSerializer)
    is_muted = PostCommentIsMutedField()
    language = PostCommentLanguageSerializer()
    hashtags = CommonHashtagSerializer(many=True)

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'text',
            'language',
            'created',
            'reactions_emoji_counts',
            'replies_count',
            'reaction',
            'is_edited',
            'is_muted',
            'hashtags',
            'id'
        )
