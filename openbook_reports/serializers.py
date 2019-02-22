from rest_framework import serializers
from django.conf import settings
from openbook_auth.models import User, UserProfile
from openbook_auth.serializers import BadgeSerializer
from openbook_circles.models import Circle
from openbook_common.models import Emoji
from openbook_common.serializers_fields.post import ReactionsEmojiCountField, ReactionField, CommentsCountField, \
    CirclesField
from openbook_communities.models import Community
from openbook_posts.models import Post, PostReaction, PostVideo, PostImage
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


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image'
        )


class PostReactionSerializer(serializers.ModelSerializer):
    emoji = PostReactionEmojiSerializer(many=False)

    class Meta:
        model = PostReaction
        fields = (
            'emoji',
            'id'
        )


class PostReactionEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'image',
            'keyword'
        )


class PostEmojiCountSerializer(serializers.Serializer):
    emoji = PostReactionEmojiSerializer(many=False)
    count = serializers.IntegerField(required=True,)


class PostCircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = (
            'id',
            'name',
            'color',
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


class AuthenticatedUserPostSerializer(serializers.ModelSerializer):
    image = PostImageSerializer(many=False)
    video = PostVideoSerializer(many=False)
    creator = PostCreatorSerializer(many=False)
    reactions_emoji_counts = ReactionsEmojiCountField(emoji_count_serializer=PostEmojiCountSerializer)
    reaction = ReactionField(reaction_serializer=PostReactionSerializer)
    comments_count = CommentsCountField()
    circles = CirclesField(circle_serializer=PostCircleSerializer)
    community = PostCommunitySerializer()

    class Meta:
        model = Post
        fields = (
            'id',
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
            'community'
        )
