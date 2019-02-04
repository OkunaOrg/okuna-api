from django.conf import settings
from rest_framework import serializers

from openbook_communities.models import Community
from openbook_communities.validators import community_name_characters_validator, community_name_exists


class DeleteCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class UpdateCommunitySerializer(serializers.Serializer):
    type = serializers.ChoiceField(allow_blank=False, choices=Community.COMMUNITY_TYPES)
    name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                 allow_blank=False,
                                 validators=[community_name_characters_validator, community_name_exists])
    title = serializers.CharField(max_length=settings.COMMUNITY_TITLE_MAX_LENGTH,
                                  allow_blank=False)
    description = serializers.CharField(max_length=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH,
                                        allow_blank=True)
    rules = serializers.CharField(max_length=settings.COMMUNITY_RULES_MAX_LENGTH,
                                  allow_blank=True)


class UpdateCommunityAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(allow_empty_file=False, required=False)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class UpdateCommunityCoverSerializer(serializers.Serializer):
    cover = serializers.ImageField(allow_empty_file=False, required=False)
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           required=True,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetCommunityCommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = (
            'title',
            'avatar',
            'cover',
            'members_count',
            'color',
            'description',
            'rules'
        )
