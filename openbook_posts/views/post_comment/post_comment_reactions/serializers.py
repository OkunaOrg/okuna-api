from rest_framework import serializers

from openbook_common.models import Emoji, EmojiGroup
from openbook_common.validators import emoji_id_exists
from openbook_posts.validators import post_uuid_exists, post_comment_id_exists, \
    post_comment_id_exists_for_post_with_uuid


class PostCommentReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image',
            'created',
        )


class PostCommentEmojiCountSerializer(serializers.Serializer):
    emoji = PostCommentReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class ReactToPostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    emoji_id = serializers.IntegerField(
        validators=[emoji_id_exists],
        required=True,
    )

    def validate(self, data):
        post_comment_id_exists_for_post_with_uuid(post_comment_id=data['post_comment_id'], post_uuid=data['post_uuid'])
        return data


class GetPostCommentReactionsEmojiCountSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )

    def validate(self, data):
        post_comment_id_exists_for_post_with_uuid(post_comment_id=data['post_comment_id'], post_uuid=data['post_uuid'])
        return data


class GetPostCommentReactionsSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    emoji_id = serializers.IntegerField(
        validators=[emoji_id_exists],
        required=False,
    )

    def validate(self, data):
        post_comment_id_exists_for_post_with_uuid(post_comment_id=data['post_comment_id'], post_uuid=data['post_uuid'])
        return data


class PostCommentReactionEmojiGroupSerializer(serializers.ModelSerializer):
    emojis = serializers.SerializerMethodField()

    def get_emojis(self, obj):
        emojis = obj.emojis.all().order_by('order')

        request = self.context['request']
        return PostCommentReactionEmojiSerializer(emojis, many=True, context={'request': request}).data

    class Meta:
        model = EmojiGroup

        fields = (
            'id',
            'keyword',
            'color',
            'order',
            'emojis',
        )
