from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_categories.models import Category
from openbook_categories.validators import category_name_exists
from openbook_common.serializers_fields.user import IsFollowingField
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community
from openbook_communities.serializers_fields import IsMemberField, IsInvitedField, IsModField, IsAdminField, \
    IsCreatorField, RulesField
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
    invites_enabled = serializers.BooleanField(required=False, allow_null=False)
    categories = serializers.ListField(
        required=False,
        min_length=settings.COMMUNITY_CATEGORIES_MIN_AMOUNT,
        max_length=settings.COMMUNITY_CATEGORIES_MAX_AMOUNT,
        child=serializers.CharField(max_length=settings.TAG_NAME_MAX_LENGTH, validators=[category_name_exists]),
    )
    color = serializers.CharField(max_length=settings.COLOR_ATTR_MAX_LENGTH, required=False,
                                  validators=[hex_color_validator])


class UpdateCommunityAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(allow_empty_file=False, required=True)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class UpdateCommunityCoverSerializer(serializers.Serializer):
    cover = serializers.ImageField(allow_empty_file=False, required=True)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class FavoriteCommunitySerializer(serializers.Serializer):
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


class GetCommunityModeratorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
            'name'
        )


class GetCommunityModeratorUserSerializer(serializers.ModelSerializer):
    profile = GetCommunityModeratorProfileSerializer(many=False)
    is_following = IsFollowingField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'is_following'
        )


class GetCommunityCommunitySerializer(serializers.ModelSerializer):
    categories = GetCommunityCommunityCategorySerializer(many=True)
    is_member = IsMemberField()
    is_invited = IsInvitedField()
    is_mod = IsModField()
    is_admin = IsAdminField()
    is_creator = IsCreatorField()
    moderators = GetCommunityModeratorUserSerializer(many=True)
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
            'type',
            'invites_enabled',
            'is_member',
            'is_invited',
            'is_admin',
            'is_mod',
            'is_creator',
        )
