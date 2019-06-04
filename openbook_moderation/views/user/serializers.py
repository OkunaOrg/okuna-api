from generic_relations.relations import GenericRelatedField
from rest_framework import serializers

from openbook_auth.models import UserProfile, User
from openbook_communities.models import Community
from openbook_moderation.models import ModerationPenalty, ModeratedObject, \
    ModerationCategory
from openbook_posts.models import Post, PostComment, PostImage


class GetUserModerationPenaltiesSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class ModerationPenaltyUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name'
        )


class ModerationPenaltyUserSerializer(serializers.ModelSerializer):
    profile = ModerationPenaltyUserProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ModerationPenaltyModeratedObjectUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name'
        )


class ModerationPenaltyModeratedObjectUserSerializer(serializers.ModelSerializer):
    profile = ModerationPenaltyModeratedObjectUserProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class ModerationPenaltyModeratedObjectCommunitySerializer(serializers.ModelSerializer):
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


class ModerationPenaltyModeratedObjectPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = (
            'id',
            'image',
            'width',
            'height'
        )


class ModerationPenaltyModeratedObjectPostSerializer(serializers.ModelSerializer):
    creator = ModerationPenaltyModeratedObjectUserSerializer()
    community = ModerationPenaltyModeratedObjectCommunitySerializer()
    image = ModerationPenaltyModeratedObjectPostImageSerializer()

    class Meta:
        model = Post
        fields = (
            'id',
            'text',
            'creator',
            'community',
            'image',
        )


class ModerationPenaltyModeratedObjectPostCommentSerializer(serializers.ModelSerializer):
    commenter = ModerationPenaltyModeratedObjectUserSerializer()
    post = ModerationPenaltyModeratedObjectPostSerializer()

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


class ModerationPenaltyModeratedObjectSerializer(serializers.ModelSerializer):
    category = ModerationCategorySerializer()

    content_object = GenericRelatedField({
        Post: ModerationPenaltyModeratedObjectPostSerializer(),
        PostComment: ModerationPenaltyModeratedObjectPostCommentSerializer(),
        Community: ModerationPenaltyModeratedObjectCommunitySerializer(),
        User: ModerationPenaltyModeratedObjectUserSerializer(),
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
        )


class ModerationPenaltySerializer(serializers.ModelSerializer):
    user = ModerationPenaltyUserSerializer()
    moderated_object = ModerationPenaltyModeratedObjectSerializer()

    class Meta:
        model = ModerationPenalty
        fields = (
            'id',
            'user',
            'expiration',
            'moderated_object',
            'type',
        )
