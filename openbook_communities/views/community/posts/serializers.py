from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Emoji, Badge
from openbook_common.serializers_fields.post import ReactionsEmojiCountField, CommentsCountField, PostCreatorField, \
    IsMutedField, ReactionField
from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_communities.models import CommunityMembership, Community
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import PostImage, PostVideo, Post, PostReaction


class GetCommunityPostsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class CreateCommunityPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=False)
    image = RestrictedImageFileSizeField(allow_empty_file=False, required=False,
                                         max_upload_size=settings.POST_IMAGE_MAX_SIZE)
    video = serializers.FileField(allow_empty_file=False, required=False)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class CommunityPostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'width',
            'height'
        )


class CommunityPostCreatorBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class CommunityPostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = CommunityPostCreatorBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges'
        )


class CommunityPostCreatorSerializer(serializers.ModelSerializer):
    profile = CommunityPostCreatorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username'
        )


class CommunityPostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = (
            'video',
        )


class CommunityPostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image'
        )


class CommunityPostEmojiCountSerializer(serializers.Serializer):
    emoji = CommunityPostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


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


class CommunityPostCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'avatar'
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


class CommunityPostSerializer(serializers.ModelSerializer):
    image = CommunityPostImageSerializer(many=False)
    video = CommunityPostVideoSerializer(many=False)
    creator = PostCreatorField(post_creator_serializer=CommunityPostCreatorSerializer,
                               community_membership_serializer=CommunityMembershipSerializer)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=CommunityPostEmojiCountSerializer)
    comments_count = CommentsCountField()
    community = CommunityPostCommunitySerializer(many=False)
    is_muted = IsMutedField()
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)

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
            'community',
            'is_muted',
            'reaction',
            'is_edited'
        )
