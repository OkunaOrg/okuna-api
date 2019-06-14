from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_communities.models import Community
from openbook_moderation.models import ModeratedObject, ModerationCategory
from openbook_posts.models import Post, PostComment, PostImage


class ModeratedObjectUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name'
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


class ModeratedObjectPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'id',
            'image',
            'width',
            'height'
        )


class ModeratedObjectPostSerializer(serializers.ModelSerializer):
    creator = ModeratedObjectUserSerializer()
    community = ModeratedObjectCommunitySerializer()
    image = ModeratedObjectPostImageSerializer()

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'creator',
            'community',
            'image',
            'created',
            'comments_enabled',
            'is_closed',
        )


class ModeratedObjectPostCommentSerializer(serializers.ModelSerializer):
    commenter = ModeratedObjectUserSerializer()
    post = ModeratedObjectPostSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
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
