from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_username_exists, username_characters_validator
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Emoji
from openbook_common.utils.model_loaders import get_post_model
from openbook_lists.validators import list_id_exists
from openbook_posts.models import PostImage, Post, PostReaction


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
    circle_id = serializers.ListField(
        required=False,
        child=serializers.IntegerField(validators=[circle_id_exists]),
    )


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
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


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'color',
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
            'color',
            'image',
            'order'
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = serializers.SerializerMethodField()
    reaction = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_reaction(self, obj):
        request = self.context['request']
        user = request.user

        try:
            reaction = user.get_reaction_for_post_with_id(obj.pk)
            return PostReactionSerializer(reaction, context={'request': request}).data
        except PostReaction.DoesNotExist:
            return None

    def get_reactions_emoji_counts(self, obj):
        request = self.context['request']
        user = request.user
        post_emoji_counts = user.get_emoji_counts_for_post_with_id(obj.pk)
        post_reactions_serializer = PostEmojiCountSerializer(post_emoji_counts, many=True,
                                                             context={"request": request, 'post': obj})
        return post_reactions_serializer.data

    def get_comments_count(self, obj):
        request = self.context['request']
        user = request.user
        return user.get_comments_count_for_post_with_id(obj.pk)

    class Meta:
        model = Post
        fields = (
            'id',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'image',
            'creator',
            'reaction',
            'public_comments',
            'public_reactions'
        )


class UnauthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_reactions_emoji_counts(self, obj):
        if not obj.public_reactions:
            return []

        request = self.context['request']
        Post = get_post_model()
        post_emoji_counts = Post.get_emoji_counts_for_post_with_id(obj.pk)
        post_reactions_serializer = PostEmojiCountSerializer(post_emoji_counts, many=True,
                                                             context={"request": request, 'post': obj})
        return post_reactions_serializer.data

    def get_comments_count(self, obj):
        if not obj.public_comments:
            return 0
        return obj.count_comments()

    class Meta:
        model = Post
        fields = (
            'id',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'image',
            'creator',
            'public_comments',
            'public_reactions'
        )
