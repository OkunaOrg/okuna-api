from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Language, Badge
from openbook_common.serializers import CommonEmojiSerializer
from openbook_common.serializers_fields.hashtag import HashtagPostsCountField
from openbook_common.serializers_fields.post import IsEncircledField
from openbook_communities.models import Community
from openbook_hashtags.models import Hashtag
from openbook_moderation.models import ModeratedObject, ModerationCategory
from openbook_posts.models import Post, PostComment, PostImage


class ModeratedObjectUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class ModeratedObjectUserProfileSerializer(serializers.ModelSerializer):
    badges = ModeratedObjectUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class ModeratedObjectUserSerializer(serializers.ModelSerializer):
    profile = ModeratedObjectUserProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ModeratedObjectCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'title',
            'avatar',
            'description',
            'color'
        )


class ModeratedObjectHashtagSerializer(serializers.ModelSerializer):
    emoji = CommonEmojiSerializer()
    posts_count = HashtagPostsCountField(show_all=True)

    class Meta:
        model = Hashtag
        fields = (
            'id',
            'name',
            'color',
            'text_color',
            'image',
            'emoji',
            'posts_count'
        )


class ModeratedObjectPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'id',
            'image',
            'thumbnail',
            'width',
            'height'
        )


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = (
            'id',
            'code',
            'name',
        )


class ModeratedObjectPostSerializer(serializers.ModelSerializer):
    creator = ModeratedObjectUserSerializer()
    community = ModeratedObjectCommunitySerializer()
    image = ModeratedObjectPostImageSerializer()
    language = LanguageSerializer()
    is_encircled = IsEncircledField()

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'language',
            'creator',
            'community',
            'image',
            'created',
            'comments_enabled',
            'is_closed',
            'is_encircled',
        )


class ModeratedObjectPostCommentSerializer(serializers.ModelSerializer):
    commenter = ModeratedObjectUserSerializer()
    post = ModeratedObjectPostSerializer()
    language = LanguageSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'language',
            'commenter',
            'commenter',
            'created',
            'post_id',
            'post',
            'is_edited'
        )


class ModerationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCategory
        fields = (
            'id',
            'name',
            'title',
            'description',
        )


class ModeratedObjectSerializer(serializers.ModelSerializer):
    category = ModerationCategorySerializer()

    content_object = GenericRelatedField({
        Post: ModeratedObjectPostSerializer(),
        PostComment: ModeratedObjectPostCommentSerializer(),
        Community: ModeratedObjectCommunitySerializer(),
        User: ModeratedObjectUserSerializer(),
        Hashtag: ModeratedObjectHashtagSerializer()
    })

    class Meta:
        model = ModeratedObject
        fields = (
            'id',
            'object_type',
            'object_id',
            'content_object',
            'verified',
            'status',
            'description',
            'category',
            'reports_count'
        )
