from rest_framework import serializers

from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_auth.serializers import BadgeSerializer
from openbook_auth.validators import user_username_exists, username_characters_validator
from openbook_circles.models import Circle
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Emoji
from openbook_common.serializers_fields.post import ReactionField, CommentsCountField, ReactionsEmojiCountField, \
    CirclesField
from openbook_communities.models import Community
from openbook_lists.validators import list_id_exists
from openbook_posts.models import PostImage, Post, PostReaction, PostVideo


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


class CreatePostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=False)
    image = serializers.ImageField(allow_empty_file=False, required=False)
    video = serializers.FileField(allow_empty_file=False, required=False)
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
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
    class Meta:
        model = PostImage
        fields = (
            'image',
        )


class PostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = (
            'video',
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


class PostCommunitySerializer(serializers.ModelSerializer):
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
        )


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()

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
            'reaction',
            'public_comments',
            'public_reactions',
            'circles',
            'community'
        )


class UnauthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
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
            'public_comments',
            'public_reactions'
        )
