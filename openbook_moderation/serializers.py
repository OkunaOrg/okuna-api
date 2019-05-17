from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_communities.models import Community
from openbook_moderation.models import ModeratedObject
from openbook_posts.models import Post, PostComment, PostImage


class ModeratedObjectUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar'
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


class ModeratedObjectPostCommentSerializer(serializers.ModelSerializer):
    commenter = ModeratedObjectUserSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'commenter',
            'commenter',
            'created',
            'post_id'
        )


class ModeratedObjectCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'avatar',
            'description'
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
        )


class ModeratedObjectSerializer(serializers.ModelSerializer):
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
            'category_id'
        )
