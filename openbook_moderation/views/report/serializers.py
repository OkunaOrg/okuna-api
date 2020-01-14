from django.conf import settings
from rest_framework import serializers

from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_communities.validators import community_name_exists, community_name_characters_validator
from openbook_hashtags.validators import hashtag_name_validator, hashtag_name_exists
from openbook_moderation.views.validators import moderation_category_id_exists, moderated_object_id_exists
from openbook_posts.validators import post_uuid_exists, post_comment_id_exists


class ReportPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)


class ReportPostCommentSerializer(serializers.Serializer):
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)


class ReportCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)


class ReportUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     required=True,
                                     validators=[username_characters_validator, user_username_exists])
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)


class ReportHashtagSerializer(serializers.Serializer):
    hashtag_name = serializers.CharField(max_length=settings.HASHTAG_NAME_MAX_LENGTH,
                                         allow_blank=False,
                                         required=True,
                                         validators=[hashtag_name_validator, hashtag_name_exists])
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)


class ReportModeratedObjectSerializer(serializers.Serializer):
    moderated_object_id = serializers.IntegerField(
        validators=[moderated_object_id_exists],
        required=True,
    )
    category_id = serializers.IntegerField(validators=[moderation_category_id_exists], required=True)
    description = serializers.CharField(max_length=settings.MODERATION_REPORT_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=False)
