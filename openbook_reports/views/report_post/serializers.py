from rest_framework import serializers
from django.conf import settings
from openbook_circles.models import Circle
from openbook_common.models import Emoji
from openbook_common.serializers_fields.post import PostReportsField, ReactionField, \
    CirclesField, CommentsCountField, IsMutedField, ReactionsEmojiCountField
from openbook_communities.models import Community
from openbook_posts.models import Post, PostVideo, PostImage, PostReaction
from openbook_posts.validators import post_uuid_exists
from openbook_reports.models import PostReport
from openbook_reports.views.common.serializers import PostReportCategorySerializer, PostCreatorSerializer
from openbook_reports.validators import is_valid_report_category, report_id_exists


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
