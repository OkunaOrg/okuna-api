from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_auth.serializers import BadgeSerializer
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Emoji, EmojiGroup
from openbook_common.serializers_fields.post import PostCreatorField, ReactionsEmojiCountField, ReactionField, \
    CommentsCountField, CirclesField, IsMutedField
from openbook_common.serializers_fields.post_comment import PostCommenterField
from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_common.validators import emoji_id_exists, emoji_group_id_exists
from openbook_communities.models import CommunityMembership, Community
from openbook_communities.serializers_fields import CommunityMembershipsField
from openbook_posts.models import PostComment, PostReaction, PostVideo, PostImage, Post
from openbook_posts.validators import post_comment_id_exists, post_reaction_id_exists, \
    post_uuid_exists


class DeletePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


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


class PostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCommenterField(post_commenter_serializer=PostCommentCommenterSerializer,
                                   community_membership_serializer=PostCommenterCommunityMembershipSerializer)

    class Meta:
        model = PostComment
        fields = (
            'commenter',
            'text',
            'created',
            'is_edited',
            'id'
        )


class EditPostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'is_edited'
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


class PostReactorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
        )


class PostReactionReactorSerializer(serializers.ModelSerializer):
    profile = PostReactorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'username',
            'profile',
            'id'
        )


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image',
            'created',
        )


class PostReactionSerializer(serializers.ModelSerializer):
    reactor = PostReactionReactorSerializer(many=False)
    emoji = PostReactionEmojiSerializer(many=False)

    class Meta:
        model = PostReaction
        fields = (
            'reactor',
            'created',
            'emoji',
            'id'
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class ReactToPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    emoji_id = serializers.IntegerField(
        validators=[emoji_id_exists],
        required=True,
    )
    group_id = serializers.IntegerField(
        validators=[emoji_group_id_exists],
        required=True,
    )


class GetPostReactionsEmojiCountSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class GetPostReactionsSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    emoji_id = serializers.IntegerField(
        validators=[emoji_id_exists],
        required=False,
    )


class DeletePostReactionSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_reaction_id = serializers.IntegerField(
        validators=[post_reaction_id_exists],
        required=True,
    )


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji

        fields = (
            'id',
            'keyword',
            'image',
            'order',
        )


class PostReactionEmojiGroupSerializer(serializers.ModelSerializer):
    emojis = serializers.SerializerMethodField()

    def get_emojis(self, obj):
        emojis = obj.emojis.all().order_by('order')

        request = self.context['request']
        return PostReactionEmojiSerializer(emojis, many=True, context={'request': request}).data

    class Meta:
        model = EmojiGroup

        fields = (
            'id',
            'keyword',
            'color',
            'order',
            'emojis',
        )


class GetPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class MutePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class UnmutePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges'
        )


class PostCreatorSerializer(serializers.ModelSerializer):
    profile = PostCreatorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username'
        )


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

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
            'video',
        )


class CommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class PostCommunitySerializer(serializers.ModelSerializer):
    memberships = CommunityMembershipsField(community_membership_serializer=CommunityMembershipSerializer)

    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'title',
            'color',
            'avatar',
            'cover',
            'user_adjective',
            'users_adjective',
            'memberships',
        )


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
        )


class GetPostPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorField(post_creator_serializer=PostCreatorSerializer,
                               community_membership_serializer=CommunityMembershipSerializer)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()
    is_muted = IsMutedField()

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'image',
            'video',
            'creator',
            'reaction',
            'public_comments',
            'public_reactions',
            'circles',
            'community',
            'is_muted',
            'is_edited'
        )


class EditPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=True)
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class AuthenticatedUserEditPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'text',
            'is_edited',
        )
