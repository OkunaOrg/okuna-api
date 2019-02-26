from rest_framework import serializers
from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_auth.serializers import BadgeSerializer
from openbook_communities.models import Community
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import Post, PostVideo, PostImage, PostComment
from openbook_posts.validators import post_id_exists, post_comment_id_exists
from openbook_reports.models import ReportCategory, PostReport, PostCommentReport
from openbook_reports.validators import is_valid_report_category, report_id_exists, comment_report_id_exsits


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
            'status',
            'comment',
            'created',
            'id'
        )


class ConfirmRejectPostReportSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    report_id = serializers.IntegerField(
        validators=[report_id_exists],
        required=True,
    )


class ConfirmRejectPostCommentReportSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
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


class PostReportConfirmRejectSerializer(serializers.ModelSerializer):
    category = PostReportCategorySerializer()

    class Meta:
        model = PostReport
        fields = (
            'category',
            'status',
            'comment',
            'created',
            'id'
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


class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = PostImage
        fields = (
            'image',
            'width',
            'height'
        )


class PostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = (
            'video',
        )


class PostCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'title',
            'color',
            'avatar',
            'cover',
            'user_adjective',
            'users_adjective',
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


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reports = PostReportSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            'id',
            'created',
            'text',
            'image',
            'video',
            'creator',
            'reports'
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
    post_id = serializers.IntegerField(
        validators=[post_id_exists],
        required=True,
    )
    category_name = serializers.CharField(max_length=settings.REPORT_CATEGORY_NAME_MAX_LENGTH, required=True,
                                          validators=[is_valid_report_category])
    comment = serializers.CharField(max_length=settings.REPORT_COMMENT_MAX_LENGTH, allow_blank=True)


class ReportPostCommentsSerializer(serializers.Serializer):
    post_comment_id = serializers.IntegerField(
        validators=[post_comment_id_exists],
        required=True,
    )

