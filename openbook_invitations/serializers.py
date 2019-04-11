from rest_framework import serializers
from openbook.settings import PROFILE_NAME_MAX_LENGTH
from openbook_invitations.models import UserInvite
from openbook_auth.models import User
from openbook_invitations.validators import invite_id_exists, check_invite_not_used


class CreateUserInviteSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH, required=True, allow_blank=False)


class GetUserInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInvite
        fields = (
            'id',
            'nickname',
            'token',
            'created_user',
            'invited_date'
        )


class GetUserInvitesSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        max_value=20
    )
    offset = serializers.IntegerField(
        required=False,
    )


class DeleteUserInviteSerializer(serializers.Serializer):
    invite_id = serializers.IntegerField(
        validators=[invite_id_exists],
        required=True,
    )


class EmailUserInviteSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    invite_id = serializers.IntegerField(
        validators=[invite_id_exists, check_invite_not_used],
        required=True,
    )
