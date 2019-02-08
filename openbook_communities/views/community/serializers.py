from django.conf import settings
from rest_framework import serializers

from openbook_categories.models import Category
from openbook_categories.validators import category_name_exists
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community
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


class UpdateCommunityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'title',
        )


class GetCommunityCommunitySerializer(serializers.ModelSerializer):
    categories = UpdateCommunityCategorySerializer(many=True)

    class Meta:
        model = Community
        fields = (
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
            'categories'
        )
