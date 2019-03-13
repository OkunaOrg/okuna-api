from rest_framework import serializers
from django.conf import settings
from rest_framework.serializers import ModelSerializer

from openbook_auth.models import User, UserProfile
from openbook_auth.serializers import BadgeSerializer
from openbook_circles.models import Circle
from openbook_common.models import Emoji
from openbook_common.serializers_fields.post import PostReportsField, PostReportCountsField, ReactionField, \
    CirclesField, CommentsCountField, IsMutedField, ReactionsEmojiCountField
from openbook_communities.models import Community
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import Post, PostVideo, PostImage, PostComment, PostReaction
from openbook_posts.validators import post_id_exists, post_comment_id_exists, post_uuid_exists
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
            'title'
        )


class ReportPostSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    category_id = serializers.IntegerField(required=True, validators=[is_valid_report_category])
    comment = serializers.CharField(max_length=settings.REPORT_COMMENT_MAX_LENGTH, allow_blank=True, required=False)


class GetPostReportSerializer(serializers.Serializer):
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )

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
    post_uuid = serializers.UUIDField(
        validators=[post_uuid_exists],
        required=True,
    )
    report_id = serializers.IntegerField(
        validators=[report_id_exists],
        required=True,
    )


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


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
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


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji

        fields = (
            'id',
            'keyword',
            'image',
            'order',
        )


class PostReactionSerializer(serializers.ModelSerializer):
    emoji = PostReactionEmojiSerializer(many=False)

    class Meta:
        model = PostReaction
        fields = (
            'emoji',
            'id'
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True, )


class PostReportCategoryCountSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=settings.REPORT_CATEGORY_TITLE_MAX_LENGTH)
    count = serializers.IntegerField()


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()
    is_muted = IsMutedField()
    reports = PostReportsField(post_report_serializer=PostReportSerializer)

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'comments_count',
            'reactions_emoji_counts',
            'created',
            'text',
            'image',
            'video',
            'creator',
            'reaction',
            'public_comments',
            'public_reactions',
            'circles',
            'community',
            'reports',
            'is_muted'
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

