from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openbook.settings import LIST_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import UserProfile, User
from openbook_lists.models import List
from openbook_lists.validators import list_name_not_taken_for_user_validator, list_with_id_exists_for_user_with_id
from openbook_common.validators import emoji_id_exists
from django.utils.translation import ugettext_lazy as _


class CreateListSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=LIST_MAX_LENGTH, required=True, allow_blank=False,
                                 validators=[])
    emoji_id = serializers.IntegerField(validators=[emoji_id_exists])

    def validate_name(self, name):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            list_name_not_taken_for_user_validator(name, user)
            return name
        else:
            raise ValidationError(
                _('A user is required.'),
            )


class DeleteListSerializer(serializers.Serializer):
    list_id = serializers.IntegerField(required=True)

    def validate_list_id(self, list_id):
        user = self.context.get("request").user
        list_with_id_exists_for_user_with_id(list_id, user.pk)


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
