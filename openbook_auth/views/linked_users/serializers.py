from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_common.models import Badge
from openbook_common.serializers_fields.user import \
    IsFollowingField, IsConnectedField, CommunitiesInvitesField, CommunitiesMembershipsField, AreNewPostNotificationsEnabledForUserField
from openbook_communities.models import CommunityMembership, CommunityInvite
from openbook_communities.serializers_fields import CommunityMembershipsField
from openbook_communities.validators import community_name_exists, community_name_characters_validator


class GetLinkedUsersSerializer(serializers.Serializer):
    max_id = serializers.IntegerField(
        required=False,
    )
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )
    with_community = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class SearchLinkedUsersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=settings.SEARCH_QUERIES_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )
    with_community = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetLinkedUsersUserCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class GetLinkedUsersUserCommunityInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityInvite
        fields = (
            'id',
            'creator_id',
            'invited_user_id',
            'community_id'
        )


class LinkedUsersUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class LinkedUsersUserProfileSerializer(serializers.ModelSerializer):
    badges = LinkedUsersUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name',
            'badges'
        )


class LinkedUsersUserSerializer(serializers.ModelSerializer):
    profile = LinkedUsersUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForUserField()
    is_connected = IsConnectedField()
    communities_memberships = CommunitiesMembershipsField(
        community_membership_serializer=GetLinkedUsersUserCommunityMembershipSerializer)
    communities_invites = CommunitiesInvitesField(
        community_invite_serializer=GetLinkedUsersUserCommunityInviteSerializer
    )

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'are_new_post_notifications_enabled',
            'is_connected',
            'communities_invites',
            'communities_memberships'
        )
