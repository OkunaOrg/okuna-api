from django.conf import settings
from rest_framework import serializers

from openbook_communities.models import Community
from openbook_communities.validators import community_name_characters_validator


class DeleteCommunitySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                 allow_blank=False, validators=[community_name_characters_validator])


class UpdateCommunitySerializer(serializers.Serializer):
    type = serializers.ChoiceField(allow_blank=False, choices=Community.COMMUNITY_TYPES)
    name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                 allow_blank=False, validators=[community_name_characters_validator])
    title = serializers.CharField(max_length=settings.COMMUNITY_TITLE_MAX_LENGTH,
                                  allow_blank=False)
    description = serializers.CharField(max_length=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH,
                                        allow_blank=True)
    rules = serializers.CharField(max_length=settings.COMMUNITY_RULES_MAX_LENGTH,
                                  allow_blank=True)


class UpdateCommunityAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(allow_empty_file=False, required=False)


class UpdateCommunityCoverSerializer(serializers.Serializer):
    cover = serializers.ImageField(allow_empty_file=False, required=False)


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
