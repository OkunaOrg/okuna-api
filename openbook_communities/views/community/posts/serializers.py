from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Emoji
from openbook_common.serializers_fields.post import ReactionsEmojiCountField, CommentsCountField
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import PostImage, PostVideo, Post


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


class CommunityPostCreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
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


class CommunityPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'image',
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


class CommunityPostSerializer(serializers.ModelSerializer):
    image = CommunityPostImageSerializer(many=False)
    video = CommunityPostVideoSerializer(many=False)
    creator = CommunityPostCreatorSerializer(many=False)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=CommunityPostEmojiCountSerializer)
    comments_count = CommentsCountField()

    class Meta:
        model = Post
        fields = (
            'id',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'image',
            'video',
            'creator',
        )
