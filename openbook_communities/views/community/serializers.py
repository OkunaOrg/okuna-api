from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_categories.models import Category
from openbook_categories.validators import category_name_exists
from openbook_common.models import Badge
from openbook_common.serializers_fields.community import IsCommunityReportedField, CommunityPostsCountField
from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_common.serializers_fields.user import IsFollowingField, AreNewPostNotificationsEnabledForUserField
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community, CommunityMembership
from openbook_communities.serializers_fields import IsInvitedField, \
    IsCreatorField, RulesField, ModeratorsField, CommunityMembershipsField, IsFavoriteField, AdministratorsField, \
    AreNewPostNotificationsEnabledForCommunityField
from openbook_communities.validators import community_name_characters_validator, community_name_exists


class GetCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class DeleteCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class UpdateCommunitySerializer(serializers.Serializer):
    # The name of the community to update
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           validators=[community_name_characters_validator, community_name_exists],
                                           required=True)
    type = serializers.ChoiceField(choices=Community.COMMUNITY_TYPES, required=False)
    name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                 validators=[community_name_characters_validator], required=False)
    title = serializers.CharField(max_length=settings.COMMUNITY_TITLE_MAX_LENGTH, required=False)
    description = serializers.CharField(max_length=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH, required=False,
                                        allow_blank=True)
    rules = serializers.CharField(max_length=settings.COMMUNITY_RULES_MAX_LENGTH, required=False, allow_blank=True)
    user_adjective = serializers.CharField(max_length=settings.COMMUNITY_USER_ADJECTIVE_MAX_LENGTH, required=False,
                                           allow_blank=True)
    users_adjective = serializers.CharField(max_length=settings.COMMUNITY_USERS_ADJECTIVE_MAX_LENGTH, required=False,
                                            allow_blank=True)
    invites_enabled = serializers.BooleanField(required=False)
    categories = serializers.ListField(
        required=False,
        min_length=settings.COMMUNITY_CATEGORIES_MIN_AMOUNT,
        max_length=settings.COMMUNITY_CATEGORIES_MAX_AMOUNT,
        child=serializers.CharField(max_length=settings.HASHTAG_NAME_MAX_LENGTH, validators=[category_name_exists]),
    )
    color = serializers.CharField(max_length=settings.COLOR_ATTR_MAX_LENGTH, required=False,
                                  validators=[hex_color_validator])


class UpdateCommunityAvatarSerializer(serializers.Serializer):
    avatar = RestrictedImageFileSizeField(allow_empty_file=False, required=True,
                                          max_upload_size=settings.COMMUNITY_AVATAR_MAX_SIZE)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class UpdateCommunityCoverSerializer(serializers.Serializer):
    cover = RestrictedImageFileSizeField(allow_empty_file=False, required=True,
                                         max_upload_size=settings.COMMUNITY_COVER_MAX_SIZE)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class FavoriteCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class TopPostCommunityExclusionSerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetCommunityCommunityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'title',
            'color'
        )


class GetCommunityStaffUserBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class GetCommunityModeratorProfileSerializer(serializers.ModelSerializer):
    badges = GetCommunityStaffUserBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'name',
            'badges'
        )


class GetCommunityStaffUserSerializer(serializers.ModelSerializer):
    profile = GetCommunityModeratorProfileSerializer(many=False)
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


class GetCommunityCommunityMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = (
            'id',
            'user_id',
            'community_id',
            'is_administrator',
            'is_moderator',
        )


class GetCommunityCommunitySerializer(serializers.ModelSerializer):
    categories = GetCommunityCommunityCategorySerializer(many=True)
    is_invited = IsInvitedField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForCommunityField()
    is_creator = IsCreatorField()
    is_favorite = IsFavoriteField()
    is_reported = IsCommunityReportedField()
    moderators = ModeratorsField(moderator_serializer=GetCommunityStaffUserSerializer)
    administrators = AdministratorsField(administrator_serializer=GetCommunityStaffUserSerializer)
    memberships = CommunityMembershipsField(community_membership_serializer=GetCommunityCommunityMembershipSerializer)
    rules = RulesField()

    class Meta:
        model = Community
        fields = (
            'id',
            'title',
            'name',
            'avatar',
            'cover',
            'members_count',
            'color',
            'description',
            'rules',
            'user_adjective',
            'users_adjective',
            'categories',
            'moderators',
            'administrators',
            'type',
            'invites_enabled',
            'is_invited',
            'are_new_post_notifications_enabled',
            'is_creator',
            'is_favorite',
            'is_reported',
            'memberships',
        )


class LegacyGetCommunityCommunitySerializer(serializers.ModelSerializer):
    categories = GetCommunityCommunityCategorySerializer(many=True)
    is_invited = IsInvitedField()
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForCommunityField()
    is_creator = IsCreatorField()
    is_favorite = IsFavoriteField()
    is_reported = IsCommunityReportedField()
    posts_count = CommunityPostsCountField()
    moderators = ModeratorsField(moderator_serializer=GetCommunityStaffUserSerializer)
    administrators = AdministratorsField(administrator_serializer=GetCommunityStaffUserSerializer)
    memberships = CommunityMembershipsField(community_membership_serializer=GetCommunityCommunityMembershipSerializer)
    rules = RulesField()

    class Meta:
        model = Community
        fields = (
            'id',
            'title',
            'name',
            'avatar',
            'cover',
            'members_count',
            'posts_count',
            'color',
            'description',
            'rules',
            'user_adjective',
            'users_adjective',
            'categories',
            'moderators',
            'administrators',
            'type',
            'invites_enabled',
            'is_invited',
            'are_new_post_notifications_enabled',
            'is_creator',
            'is_favorite',
            'is_reported',
            'memberships',
        )


class CommunityAvatarCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'avatar',
        )


class CommunityCoverCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'id',
            'name',
            'cover',
        )


class FavoriteCommunityCommunitySerializer(serializers.ModelSerializer):
    is_favorite = IsFavoriteField()

    class Meta:
        model = Community
        fields = (
            'id',
            'is_favorite',
        )


class SubscribeToCommunityNotificationsSerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class SubscribeToCommunityNotificationsCommunitySerializer(serializers.ModelSerializer):
    are_new_post_notifications_enabled = AreNewPostNotificationsEnabledForCommunityField()

    class Meta:
        model = Community
        fields = (
            'id',
            'are_new_post_notifications_enabled',
        )
