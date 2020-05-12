from rest_framework import serializers
from django.conf import settings

from openbook.settings import USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, PROFILE_NAME_MAX_LENGTH
from openbook_auth.models import UserNotificationsSettings
from openbook_auth.validators import username_characters_validator, \
    username_not_taken_validator, email_not_taken_validator, user_email_exists, user_username_exists
from django.contrib.auth.password_validation import validate_password

from openbook_common.serializers_fields.request import RestrictedImageFileSizeField
from openbook_common.validators import name_characters_validator


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password])
    is_of_legal_age = serializers.BooleanField()
    are_guidelines_accepted = serializers.BooleanField()
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH,
                                 allow_blank=False, validators=[name_characters_validator])
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     required=False,
                                     allow_blank=True,
                                     validators=[username_characters_validator, username_not_taken_validator])
    avatar = RestrictedImageFileSizeField(allow_empty_file=True, required=False,
                                          max_upload_size=settings.PROFILE_AVATAR_MAX_SIZE)
    email = serializers.EmailField(validators=[email_not_taken_validator])
    token = serializers.CharField()


class RegisterTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, username_not_taken_validator])


class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_not_taken_validator])


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator])
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class AuthenticatedUserNotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationsSettings
        fields = (
            'id',
            'post_comment_notifications',
            'post_reaction_notifications',
            'follow_notifications',
            'follow_request_notifications',
            'follow_request_approved_notifications',
            'connection_request_notifications',
            'connection_confirmed_notifications',
            'community_invite_notifications',
            'community_new_post_notifications',
            'user_new_post_notifications',
            'post_comment_reaction_notifications',
            'post_comment_reply_notifications',
            'post_comment_user_mention_notifications',
            'post_user_mention_notifications',
        )


class UpdateAuthenticatedUserNotificationsSettingsSerializer(serializers.Serializer):
    post_comment_notifications = serializers.BooleanField(required=False)
    post_reaction_notifications = serializers.BooleanField(required=False)
    follow_notifications = serializers.BooleanField(required=False)
    follow_request_notifications = serializers.BooleanField(required=False)
    follow_request_approved_notifications = serializers.BooleanField(required=False)
    connection_request_notifications = serializers.BooleanField(required=False)
    connection_confirmed_notifications = serializers.BooleanField(required=False)
    community_invite_notifications = serializers.BooleanField(required=False)
    community_new_post_notifications = serializers.BooleanField(required=False)
    user_new_post_notifications = serializers.BooleanField(required=False)
    post_comment_reaction_notifications = serializers.BooleanField(required=False)
    post_comment_reply_notifications = serializers.BooleanField(required=False)
    post_comment_user_mention_notifications = serializers.BooleanField(required=False)
    post_user_mention_notifications = serializers.BooleanField(required=False)


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[user_email_exists])


class VerifyPasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                         validators=[validate_password])
