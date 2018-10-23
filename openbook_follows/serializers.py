from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openbook_auth.models import User, UserProfile
from openbook_auth.validators import user_id_exists
from openbook_lists.validators import list_id_exists
from django.utils.translation import ugettext_lazy as _

from openbook_follows.models import Follow
from openbook_follows.validators import follow_does_not_exist, follow_with_id_exists_for_user


class CreateFollowSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, validators=[user_id_exists])
    list_id = serializers.IntegerField(required=True, validators=[list_id_exists])

    def validate_user_id(self, user_id):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            # Check follow is not with oneself
            if user.pk == user_id:
                raise ValidationError(
                    _('You cannot follow yourself.'),
                )
            else:
                # Check follow does not already exist
                follow_does_not_exist(user.pk, user_id)
            return user_id
        else:
            raise ValidationError(
                _('A user is required.'),
            )


class FollowUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'birth_date'
        )


class FollowUserSerializer(serializers.ModelSerializer):
    profile = FollowUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile'
        )


class FollowSerializer(serializers.ModelSerializer):
    followed_user = FollowUserSerializer(many=False)

    class Meta:
        model = Follow
        fields = (
            'id',
            'user',
            'list',
            'followed_user',
        )


class DeleteFollowSerializer(serializers.Serializer):
    follow_id = serializers.IntegerField(required=True)

    def validate_follow_id(self, follow_id):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            follow_with_id_exists_for_user(follow_id, user)
            return follow_id
        else:
            raise ValidationError(
                _('A user is required.'),
            )
