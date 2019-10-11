from django.conf import settings
from rest_framework import serializers

from openbook.settings import LIST_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_auth.validators import username_characters_validator, user_username_exists
from openbook_common.models import Emoji, Badge
from openbook_lists.models import List
from openbook_common.validators import emoji_id_exists
from openbook_lists.validators import list_id_exists


class CreateListSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=LIST_MAX_LENGTH, required=True, allow_blank=False)
    emoji_id = serializers.IntegerField(validators=[emoji_id_exists])


class DeleteListSerializer(serializers.Serializer):
    list_id = serializers.IntegerField(required=True, validators=[list_id_exists])


class UpdateListSerializer(serializers.Serializer):
    list_id = serializers.IntegerField(required=False, validators=[list_id_exists])
    name = serializers.CharField(max_length=LIST_MAX_LENGTH, required=False, allow_blank=False)
    emoji_id = serializers.IntegerField(validators=[emoji_id_exists], required=False)
    usernames = serializers.ListSerializer(
        required=False,
        allow_empty=True,
        child=serializers.CharField(max_length=settings.USERNAME_MAX_LENGTH,
                                    allow_blank=False,
                                    required=False,
                                    validators=[username_characters_validator, user_username_exists])
    )


class ListUserProfileBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = (
            'keyword',
            'keyword_description'
        )


class ListUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    badges = ListUserProfileBadgeSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'avatar',
            'badges'
        )


class ListUserSerializer(serializers.ModelSerializer):
    profile = ListUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
        )


class ListEmojiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emoji
        fields = (
            'id',
            'keyword',
            'image',
        )


class GetListsListSerializer(serializers.ModelSerializer):
    emoji = ListEmojiSerializer(many=False)

    class Meta:
        model = List
        fields = (
            'id',
            'name',
            'emoji',
            'follows_count'
        )


class ListNameCheckSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=LIST_MAX_LENGTH, required=True, allow_blank=False, validators=[])


class GetListListSerializer(serializers.ModelSerializer):
    emoji = ListEmojiSerializer(many=False)
    users = ListUserSerializer(many=True)

    class Meta:
        model = List
        fields = (
            'id',
            'name',
            'emoji',
            'follows_count',
            'users'
        )
