from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_circles.models import Circle
from openbook_common.models import Badge, Language
from openbook_common.serializers_fields.post import PostCreatorField, PostReactionsEmojiCountField, ReactionField, \
    CommentsCountField, CirclesField, PostIsMutedField
from openbook_communities.models import CommunityMembership, Community
from openbook_communities.serializers_fields import CommunityMembershipsField
from openbook_posts.models import PostVideo, PostImage, Post
from openbook_posts.validators import post_uuid_exists

from openbook_posts.views.post_reaction.serializers import PostReactionSerializer
from openbook_posts.views.post_reactions.serializers import PostEmojiCountSerializer


class DeletePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
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


class PostCreatorProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = PostCreatorProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges'
        )


class PostLanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
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
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()
    is_muted = PostIsMutedField()
    language = PostLanguageSerializer()

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
            'language',
            'comments_enabled',
            'public_reactions',
            'circles',
            'community',
            'is_muted',
            'is_edited',
            'is_closed',
        )


class EditPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=True)
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class AuthenticatedUserEditPostSerializer(serializers.ModelSerializer):
    language = PostLanguageSerializer()

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'text',
            'language',
            'is_edited',
        )


class ClosePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class OpenPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class OpenClosePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'is_closed',
        )
