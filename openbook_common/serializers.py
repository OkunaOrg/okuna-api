from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Emoji, EmojiGroup, Badge, Language
from openbook_common.serializers_fields.hashtag import HashtagPostsCountField
from openbook_communities.models import Community, CommunityMembership
from openbook_hashtags.models import Hashtag
from openbook_posts.models import PostReaction, PostImage


class CommonEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji

        fields = (
            'id',
            'keyword',
            'image',
            'created',
            'order',
        )


class CommonEmojiGroupSerializer(serializers.ModelSerializer):
    emojis = serializers.SerializerMethodField()

    def get_emojis(self, obj):
        emojis = obj.emojis.all().order_by('order')

        request = self.context['request']
        return CommonEmojiSerializer(emojis, many=True, context={'request': request}).data

    class Meta:
        model = EmojiGroup

        fields = (
            'id',
            'keyword',
            'color',
            'created',
            'order',
            'emojis',
        )


class CommonUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class CommonPostCreatorBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class CommonPostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = CommonPostCreatorBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'name',
            'cover',
            'badges'
        )


class CommonPostCreatorSerializer(serializers.ModelSerializer):
    profile = CommonPostCreatorProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username'
        )


class CommonPostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image'
        )


class CommonPostEmojiCountSerializer(serializers.Serializer):
    emoji = CommonPostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class CommonPostCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'avatar'
        )


class CommonPostReactionSerializer(serializers.ModelSerializer):
    emoji = CommonPostReactionEmojiSerializer(many=False)

    class Meta:
        model = PostReaction
        fields = (
            'emoji',
            'id'
        )


class CommonPostLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
        )


class CommonPostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'thumbnail',
            'width',
            'height'
        )


class CommonCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class CommonHashtagSerializer(serializers.ModelSerializer):
    posts_count = HashtagPostsCountField()
    emoji = CommonEmojiSerializer()

    class Meta:
        model = Hashtag
        fields = (
            'id',
            'name',
            'color',
            'image',
            'posts_count',
            'emoji'
        )


class ProxyDomainCheckSerializer(serializers.Serializer):
    url = serializers.CharField(
        required=True,
    )
