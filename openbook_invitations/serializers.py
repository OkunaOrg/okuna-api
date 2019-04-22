from django.conf import settings
from rest_framework import serializers
from openbook.settings import PROFILE_NAME_MAX_LENGTH
from openbook_common.models import Badge
from openbook_invitations.models import UserInvite
from openbook_auth.models import User, UserProfile
from openbook_invitations.validators import invite_id_exists, check_invite_not_used


class CreateUserInviteSerializer(serializers.Serializer):
    nickname = serializers.CharField(
        max_length=PROFILE_NAME_MAX_LENGTH,
        required=True,
        allow_blank=False)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class InvitedUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    badges = BadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'avatar',
            'bio',
            'url',
            'location',
            'cover',
            'is_of_legal_age',
            'followers_count_visible',
            'badges'
        )


class InvitedUserSerializer(serializers.ModelSerializer):
    profile = InvitedUserProfileSerializer()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class GetUserInviteSerializer(serializers.ModelSerializer):
    created_user = InvitedUserSerializer(many=False)

    class Meta:
        model = UserInvite
        fields = (
            'id',
            'email',
            'is_invite_email_sent',
            'nickname',
            'token',
            'created_user',
            'created'
        )


class GetUserInvitesSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    offset = serializers.IntegerField(
        required=False,
    )
    pending = serializers.BooleanField(required=False)


class SearchUserInvitesSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    pending = serializers.BooleanField(required=False)
    query = serializers.CharField(
        max_length=settings.SEARCH_QUERIES_MAX_LENGTH,
        allow_blank=False,
        required=True
    )


class DeleteUserInviteSerializer(serializers.Serializer):
    invite_id = serializers.IntegerField(
        validators=[invite_id_exists],
        required=True,
    )


class EditUserInviteSerializer(serializers.Serializer):
    invite_id = serializers.IntegerField(
        validators=[check_invite_not_used, invite_id_exists],
        required=True,
    )
    nickname = serializers.CharField(
        max_length=PROFILE_NAME_MAX_LENGTH,
        required=True,
        allow_blank=False)


class EmailUserInviteSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    invite_id = serializers.IntegerField(
        validators=[check_invite_not_used, invite_id_exists],
        required=True,
    )
