from rest_framework import serializers

from openbook.settings import LIST_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_lists.models import List
from openbook_common.validators import emoji_id_exists
from openbook_lists.validators import list_id_exists


class CreateListSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=LIST_MAX_LENGTH, required=True, allow_blank=False)
    emoji_id = serializers.IntegerField(validators=[emoji_id_exists])


class DeleteListSerializer(serializers.Serializer):
    list_id = serializers.IntegerField(required=True, validators=[list_id_exists])


class ListUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class ListUserSerializer(serializers.ModelSerializer):
    profile = ListUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'profile',
        )


class ListSerializer(serializers.ModelSerializer):
    users = ListUserSerializer(many=True)

    class Meta:
        model = List
        fields = (
            'id',
            'name',
            'emoji',
            'users'
        )
