from django.conf import settings
from rest_framework import serializers

from openbook_common.serializers import CommonPublicUserSerializer, \
    CommonCommunityMembershipSerializer, CommonPostEmojiCountSerializer, CommonPostCommunitySerializer, \
    CommonPostReactionSerializer, CommonPostLanguageSerializer, CommonHashtagSerializer, CommonPostLinkSerializer
from openbook_common.serializers_fields.community import CommunityPostsCountField
from openbook_common.serializers_fields.post import PostReactionsEmojiCountField, CommentsCountField, PostCreatorField, \
    PostIsMutedField, ReactionField
from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_communities.models import Community
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_posts.models import Post
from openbook_posts.validators import post_text_validators


class GetCommunityPostsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class CreateCommunityPostSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=settings.POST_MAX_LENGTH, required=False, allow_blank=False,
                                 validators=post_text_validators)
    image = RestrictedImageFileSizeField(allow_empty_file=False, required=False,
                                         max_upload_size=settings.POST_MEDIA_MAX_SIZE)
    video = serializers.FileField(allow_empty_file=False, required=False)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])
    is_draft = serializers.BooleanField(default=False)


class CommunityPostSerializer(serializers.ModelSerializer):
    # Temp backwards compat
    creator = PostCreatorField(post_creator_serializer=CommonPublicUserSerializer,
                               community_membership_serializer=CommonCommunityMembershipSerializer)
    reactions_emoji_counts = PostReactionsEmojiCountField(emoji_count_serializer=CommonPostEmojiCountSerializer)
    comments_count = CommentsCountField()
    community = CommonPostCommunitySerializer(many=False)
    is_muted = PostIsMutedField()
    reaction = ReactionField(reaction_serializer=CommonPostReactionSerializer)
    language = CommonPostLanguageSerializer()
    hashtags = CommonHashtagSerializer(many=True)
    links = CommonPostLinkSerializer(many=True)

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
            'hashtags',
            'links'
        )


class GetCommunityPostsCountsSerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetCommunityPostsCountCommunitySerializer(serializers.ModelSerializer):
    posts_count = CommunityPostsCountField()

    class Meta:
        model = Community
        fields = (
            'id',
            'posts_count',
        )
