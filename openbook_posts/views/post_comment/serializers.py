from rest_framework import serializers
from django.conf import settings
from openbook_posts.models import PostComment
from openbook_posts.validators import post_comment_id_exists, post_uuid_exists, \
    post_comment_id_exists_for_post_with_uuid
from openbook_posts.views.posts.serializers import PostLanguageSerializer


class EditPostCommentSerializer(serializers.ModelSerializer):
    language = PostLanguageSerializer()

    class Meta:
        model = PostComment
        fields = (
            'id',
            'text',
            'language',
            'is_edited'
        )


class DeletePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )


class UpdatePostCommentSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    text = serializers.CharField(max_length=settings.POST_COMMENT_MAX_LENGTH, required=True, allow_blank=False)


class MutePostCommentSerializer(serializers.Serializer):
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


class UnmutePostCommentSerializer(MutePostCommentSerializer):
    pass
