from django.conf import settings
from rest_framework import serializers

from openbook_common.serializers import CommonPostImageSerializer, CommonPostCreatorSerializer, \
    CommonCommunityMembershipSerializer, CommonPostEmojiCountSerializer, CommonPostCommunitySerializer, \
    CommonPostReactionSerializer, CommonPostLanguageSerializer
from openbook_common.serializers_fields.post import ReactionField, CommentsCountField, PostCreatorField, \
    PostReactionsEmojiCountField, PostIsMutedField
from openbook_hashtags.models import Hashtag
from openbook_hashtags.validators import hashtag_name_exists
from openbook_posts.models import Post


class GetHashtagSerializer(serializers.Serializer):
    hashtag_name = serializers.CharField(max_length=settings.HASHTAG_NAME_MAX_LENGTH, required=True, validators=[
        hashtag_name_exists
    ])


class GetHashtagsHashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = (
            'id',
            'name',
            'color',
            'image'
        )


class GetHashtagPostsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    hashtag_name = serializers.CharField(max_length=settings.HASHTAG_NAME_MAX_LENGTH,
                                         allow_blank=False,
                                         validators=[hashtag_name_exists])


class GetHashtagPostsPostSerializer(serializers.ModelSerializer):
    # Temp backwards compat
    creator = PostCreatorField(post_creator_serializer=CommonPostCreatorSerializer,
                               community_membership_serializer=CommonCommunityMembershipSerializer)
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=CommonPostEmojiCountSerializer)
    comments_count = CommentsCountField()
    community = CommonPostCommunitySerializer(many=False)
    is_muted = PostIsMutedField()
    reaction = ReactionField(reaction_serializer=CommonPostReactionSerializer)
    language = CommonPostLanguageSerializer()

    class Meta:
        model = Post
        fields = (
            'id',
            'uuid',
            'comments_count',
            'comments_enabled',
            'reactions_emoji_counts',
            'created',
            'text',
            'language',
            'creator',
            'community',
            'is_muted',
            'reaction',
            'is_edited',
            'is_closed',
            'media_height',
            'media_width',
            'media_thumbnail',
        )