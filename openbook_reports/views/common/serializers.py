from rest_framework import serializers
from django.conf import settings

from openbook_auth.models import User, UserProfile
from openbook_auth.serializers import BadgeSerializer
from openbook_reports.models import ReportCategory


class PostCreatorProfileSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'cover',
            'badges'
        )


class PostCreatorSerializer(serializers.ModelSerializer):
    profile = PostCreatorProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username'
        )


class GetReportCategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportCategory
        fields = (
            'id',
            'name',
            'title',
            'description'
        )


class PostReportCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportCategory
        fields = (
            'name',
            'title'
        )


class PostReportCategoryCountSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=settings.REPORT_CATEGORY_TITLE_MAX_LENGTH)
    count = serializers.IntegerField()


