from rest_framework import serializers

from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_circles.validators import circle_id_exists
from openbook_common.models import Emoji
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


class PostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    commented = serializers.SerializerMethodField()
    reacted = serializers.SerializerMethodField()
    reactions_emoji_counts = serializers.SerializerMethodField()
    reaction = serializers.SerializerMethodField()

    def get_commented(self, obj):
        user = self.context['request'].user
        return user.has_commented_post_with_id(obj.pk)

    def get_reacted(self, obj):
        user = self.context['request'].user
        return user.has_reacted_to_post_with_id(obj.pk)

    def get_reaction(self, obj):
        request = self.context['request']
        user = request.user

        try:
            reaction = user.get_reaction_for_post_with_id(obj.pk)
            return PostReactionSerializer(reaction).data
        except PostReaction.DoesNotExist:
            return None

    def get_reactions_emoji_counts(self, obj):
        request = self.context['request']
        user = request.user
        post_emoji_counts = user.get_emoji_counts_for_post_with_id(obj.pk)
        post_reactions_serializer = PostEmojiCountSerializer(post_emoji_counts, many=True,
                                                             context={"request": request, 'post': obj})
        return post_reactions_serializer.data

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
            'commented',
            'reacted',
            'reaction'
        )
