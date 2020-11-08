from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import UserProfile, User
from openbook_circles.models import Circle
from openbook_common.models import Badge, Language
from openbook_common.serializers import CommonHashtagSerializer, CommonPublicUserSerializer, CommonPostLinkSerializer
from openbook_common.serializers_fields.post import PostCreatorField, PostReactionsEmojiCountField, ReactionField, \
    CommentsCountField, CirclesField, PostIsMutedField, IsEncircledField
from openbook_communities.models import CommunityMembership, Community
from openbook_communities.serializers_fields import CommunityMembershipsField
from openbook_posts.models import PostImage, Post, PostLink
from openbook_posts.validators import post_uuid_exists, post_text_validators

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


class PostLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
        )


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = PostCreatorProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges',
            'name'
        )


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'thumbnail',
            'width',
            'height'
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
    creator = PostCreatorField(post_creator_serializer=CommonPublicUserSerializer,
                               community_membership_serializer=CommunityMembershipSerializer)
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()
    is_muted = PostIsMutedField()
    language = PostLanguageSerializer()
    is_encircled = IsEncircledField()
    hashtags = CommonHashtagSerializer(many=True)
    links = CommonPostLinkSerializer(many=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'creator',
            'reaction',
            'language',
            'comments_enabled',
            'public_reactions',
            'circles',
            'community',
            'hashtags',
            'links',
            'is_muted',
            'is_edited',
            'is_closed',
            'is_encircled',
            'media_height',
            'media_width',
            'media_thumbnail',
        )


class EditPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=True,
                                 validators=post_text_validators)
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class AuthenticatedUserEditPostSerializer(serializers.ModelSerializer):
    language = PostLanguageSerializer()
    hashtags = CommonHashtagSerializer(many=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'text',
            'language',
            'is_edited',
            'hashtags'
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


class TranslatePostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class SearchPostParticipantsSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    query = serializers.CharField(
        max_length=settings.SEARCH_QUERIES_MAX_LENGTH,
        required=True
    )
    count = serializers.IntegerField(
        required=False,
        default=10,
        max_value=10
    )


class GetPostParticipantsSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    count = serializers.IntegerField(
        required=False,
        default=10,
        max_value=20
    )


class PostParticipantProfileSerializer(serializers.ModelSerializer):
    badges = PostCreatorProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges',
            'name'
        )


class PostParticipantSerializer(serializers.ModelSerializer):
    profile = PostCreatorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username'
        )


class OpenClosePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'is_closed',
        )


class PublishPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )


class GetPostStatusSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
