from django.conf import settings
from rest_framework import serializers

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_communities.validators import community_name_characters_validator, community_name_exists


class JoinCommunitySerializer(serializers.Serializer):
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class RemoveCommunityMemberSerializer(serializers.Serializer):
    member_username = serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                            allow_blank=False,
                                            validators=[username_characters_validator, user_username_exists])
    community_name = serializers.CharField(max_length=settings.COMMUNITY_NAME_MAX_LENGTH,
                                           allow_blank=False,
                                           validators=[community_name_characters_validator, community_name_exists])


class GetCommunityMembersSerializer(serializers.Serializer):
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


class GetCommunityMembersMemberProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'avatar',
        )


class GetCommunityMembersMemberSerializer(serializers.ModelSerializer):
    profile = GetCommunityMembersMemberProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )
