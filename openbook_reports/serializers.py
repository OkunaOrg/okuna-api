from rest_framework import serializers
from django.conf import settings
from openbook_posts.validators import post_id_exists
from openbook_reports.models import ReportCategory, PostReport
from openbook_reports.validators import is_valid_report_category, report_id_exists


class GetReportCategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportCategory
        fields = (
            'name',
            'title',
            'description'
        )


class PostReportCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportCategory
        fields = (
            'name',
        )


class ReportPostSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    category_name = serializers.CharField(max_length=settings.REPORT_CATEGORY_NAME_MAX_LENGTH, required=True,
                                          validators=[is_valid_report_category])
    comment = serializers.CharField(max_length=settings.REPORT_COMMENT_MAX_LENGTH, allow_blank=True)


class PostReportSerializer(serializers.ModelSerializer):
    category = PostReportCategorySerializer()

    class Meta:
        model = PostReport
        fields = (
            'category',
            'comment',
            'created',
            'id'
        )


class ConfirmPostReportSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    report_id = serializers.IntegerField(
        validators=[report_id_exists],
        required=True,
    )


class PostReportConfirmSerializer(serializers.ModelSerializer):
    category = PostReportCategorySerializer()
    status = serializers.SerializerMethodField()

    class Meta:
        model = PostReport
        fields = (
            'category',
            'status',
            'comment',
            'created',
            'id'
        )

    def get_status(self, post_report):
        return post_report.status
