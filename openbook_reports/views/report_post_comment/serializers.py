from rest_framework import serializers
from django.conf import settings

from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import PostComment
from openbook_posts.validators import post_comment_id_exists, post_uuid_exists
from openbook_reports.models import PostCommentReport
from openbook_reports.views.common.serializers import PostReportCategorySerializer, PostCreatorSerializer
from openbook_reports.validators import is_valid_report_category, comment_report_id_exsits


class ConfirmRejectPostCommentReportSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    report_id = serializers.IntegerField(
        validators=[comment_report_id_exsits],
        required=True
    )


class PostCommentReportConfirmRejectSerializer(serializers.ModelSerializer):
    category = PostReportCategorySerializer()

    class Meta:
        model = PostCommentReport
        fields = (
            'category',
            'status',
            'comment',
            'created',
            'id'
        )


class PostReportCommentSerializer(serializers.ModelSerializer):
    category = PostReportCategorySerializer()

    class Meta:
        model = PostCommentReport
        fields = (
            'category',
            'status',
            'comment',
            'created',
            'id'
        )


class AuthenticatedUserPostCommentSerializer(serializers.ModelSerializer):
    commenter = PostCreatorSerializer(many=False)
    reports = PostReportCommentSerializer(many=True, read_only=True)

    class Meta:
        model = PostComment
        fields = (
            'id',
            'created',
            'text',
            'commenter',
            'reports'
        )


class ReportedPostsCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class ReportPostCommentSerializer(serializers.Serializer):
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    category_id = serializers.IntegerField(required=True, validators=[is_valid_report_category])
    comment = serializers.CharField(max_length=settings.REPORT_COMMENT_MAX_LENGTH, allow_blank=True)


class ReportPostCommentsSerializer(serializers.Serializer):
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )

