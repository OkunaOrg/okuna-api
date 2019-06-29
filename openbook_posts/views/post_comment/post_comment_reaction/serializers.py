from rest_framework import serializers

from openbook_auth.models import UserProfile, User
from openbook_common.models import Emoji
from openbook_posts.models import PostCommentReaction
from openbook_posts.validators import post_uuid_exists, post_comment_id_exists, \
    post_comment_reaction_id_exists_for_post_with_uuid_and_comment_with_id, \
    post_comment_reaction_id_exists


class DeletePostCommentReactionSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    post_comment_reaction_id = serializers.IntegerField(
        validators=[post_comment_reaction_id_exists],
        required=True,
    )

    def validate(self, data):
        post_comment_reaction_id_exists_for_post_with_uuid_and_comment_with_id(
            post_comment_reaction_id=data['post_comment_reaction_id'],
            post_comment_id=data['post_comment_id'],
            post_uuid=data['post_uuid'])
        return data


class PostReactorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'id'
        )


class PostCommentReactionReactorSerializer(serializers.ModelSerializer):
    profile = PostReactorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'username',
            'profile',
            'id'
        )


class PostCommentReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image',
            'created',
        )


class PostCommentReactionSerializer(serializers.ModelSerializer):
    reactor = PostCommentReactionReactorSerializer(many=False)
    emoji = PostCommentReactionEmojiSerializer(many=False)

    class Meta:
        model = PostCommentReaction
        fields = (
            'reactor',
            'created',
            'emoji',
            'id'
        )
