from rest_framework import serializers

from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_username_exists, username_characters_validator
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Emoji, Badge
from openbook_common.serializers_fields.post import ReactionField, CommentsCountField, PostReactionsEmojiCountField, \
    CirclesField, PostCreatorField, PostIsMutedField, IsEncircledField
from openbook_common.serializers_fields.request import RestrictedImageFileSizeField, RestrictedFileSizeField
from openbook_common.models import Language
from openbook_communities.models import Community, CommunityMembership
from openbook_communities.serializers_fields import CommunityMembershipsField
from openbook_lists.validators import list_id_exists
from openbook_posts.models import PostImage, Post, PostReaction, TopPost


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
    min_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    username = serializers.CharField(
        max_length=settings.USERNAME_MAX_LENGTH,
        allow_blank=False,
        validators=[
            username_characters_validator,
            user_username_exists
        ],
        required=False
    )


class GetTopPostsSerializer(serializers.Serializer):
    exclude_joined_communities = serializers.BooleanField(required=False)
    max_id = serializers.IntegerField(
        required=False,
    )
    min_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=False)
    # Prefer adding images with post/uuid/images
    image = RestrictedImageFileSizeField(allow_empty_file=False, required=False,
                                         max_upload_size=settings.POST_MEDIA_MAX_SIZE)
    # Prefer adding videos with post/uuid/videos
    video = RestrictedFileSizeField(allow_empty_file=False, required=False,
                                    max_upload_size=settings.POST_MEDIA_MAX_SIZE)
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )
    is_draft = serializers.BooleanField(
        default=False)


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
            'badges',
            'name'
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


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image'
        )


class PostReactionSerializer(serializers.ModelSerializer):
    emoji = PostReactionEmojiSerializer(many=False)

    class Meta:
        model = PostReaction
        fields = (
            'emoji',
            'id'
        )


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'image',
            'keyword'
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
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
            'avatar',
            'title',
            'cover',
            'color',
            'memberships',
        )


class PostLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
        )


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True, required=False, allow_empty_file=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'width',
            'height'
        )


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    creator = PostCreatorField(post_creator_serializer=PostCreatorSerializer,
                               community_membership_serializer=CommunityMembershipSerializer)
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()
    is_muted = PostIsMutedField()
    language = PostLanguageSerializer()
    is_encircled = IsEncircledField()

    # Temp backwards compat
    image = PostImageSerializer(many=False)

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
            'comments_enabled',
            'public_reactions',
            'circles',
            'community',
            'language',
            'is_muted',
            'is_encircled',
            'is_edited',
            'is_closed',
            'media_height',
            'media_width',
            'media_thumbnail',
            # Temp backwards compat
            'image',
        )


class AuthenticatedUserTopPostSerializer(serializers.ModelSerializer):
    post = AuthenticatedUserPostSerializer()

    class Meta:
        model = TopPost
        fields = (
            'id',
            'post',
            'created'
        )


class UnauthenticatedUserPostSerializer(serializers.ModelSerializer):
    creator = PostCreatorField(post_creator_serializer=PostCreatorSerializer,
                               community_membership_serializer=CommunityMembershipSerializer)
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    comments_count = CommentsCountField()
    language = PostLanguageSerializer()

    # Temp backwards compat
    image = PostImageSerializer(many=False)

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
            'language',
            'comments_enabled',
            'public_reactions',
            'is_edited',
            'media_height',
            'media_width',
            'media_thumbnail',
            # Temp backwards compat
            'image',
        )
