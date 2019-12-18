from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_common.serializers_fields.user import IsFollowingField, AreNewPostNotificationsEnabledForUserField
from openbook_communities.serializers_fields import UserCommunitiesMembershipsField
from openbook_communities.validators import community_name_characters_validator, community_name_exists
from openbook_communities.views.community.banned_users.serializers import CommunityBadgeSerializer


class AddCommunityModeratorSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists])
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class RemoveCommunityModeratorSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists])
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetCommunityModeratorsSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )


class GetCommunityModeratorsUserSerializerUserProfileSerializer(serializers.ModelSerializer):
    badges = CommunityBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'name',
            'badges'
        )


class GetCommunityModeratorsUserSerializer(serializers.ModelSerializer):
    profile = GetCommunityModeratorsUserSerializerUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'is_following',
            'are_new_post_notifications_enabled',
        )


class SearchCommunityModeratorsSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    query = serializers.CharField(
        max_length=settings.SEARCH_QUERIES_MAX_LENGTH,
        allow_blank=False,
        required=True
    )
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])
