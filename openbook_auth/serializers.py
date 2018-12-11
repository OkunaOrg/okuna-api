from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext as _

from openbook.settings import USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, PROFILE_NAME_MAX_LENGTH
from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, \
    username_not_taken_validator, email_not_taken_validator, user_username_exists
from django.contrib.auth.password_validation import validate_password

from openbook_common.serializers_fields import IsFollowingField, IsConnectedField, FollowersCountField, \
    FollowingCountField, PostsCountField
from openbook_common.validators import name_characters_validator


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password])
    birth_date = serializers.DateField(input_formats=["%d-%m-%Y"])
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     validators=[username_characters_validator, username_not_taken_validator],
                                     allow_blank=False)
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH,
                                 allow_blank=False, validators=[name_characters_validator])
    avatar = serializers.ImageField(allow_empty_file=True, required=False)
    email = serializers.EmailField(validators=[email_not_taken_validator])


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


class GetAuthenticatedUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

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
            'birth_date',
            'followers_count_visible'
        )


class GetAuthenticatedUserSerializer(serializers.ModelSerializer):
    profile = GetAuthenticatedUserProfileSerializer(many=False)
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    def get_following_count(self, obj):
        return obj.count_following()

    def get_followers_count(self, obj):
        return obj.count_followers()

    def get_posts_count(self, obj):
        return obj.count_posts()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'profile',
            'posts_count',
            'followers_count',
            'following_count'
        )


class UpdateAuthenticatedUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator],
                                     required=False)
    avatar = serializers.ImageField(allow_empty_file=False, required=False, allow_null=True)
    cover = serializers.ImageField(allow_empty_file=False, required=False, allow_null=True)
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password], required=False, allow_blank=False)
    birth_date = serializers.DateField(input_formats=["%d-%m-%Y"], required=False, allow_null=False)
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH,
                                 required=False,
                                 allow_blank=False, validators=[name_characters_validator])
    followers_count_visible = serializers.BooleanField(required=False, default=None, allow_null=True)
    bio = serializers.CharField(max_length=settings.PROFILE_BIO_MAX_LENGTH, required=False,
                                allow_blank=True)
    url = serializers.URLField(required=False,
                               allow_blank=True)
    location = serializers.CharField(max_length=settings.PROFILE_LOCATION_MAX_LENGTH, required=False,
                                     allow_blank=True)


class UpdateUserSettingsSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                         validators=[validate_password], required=False, allow_blank=False)
    current_password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                             validators=[validate_password], required=False, allow_blank=False)
    email = serializers.EmailField(validators=[email_not_taken_validator], required=False)

    def validate(self, data):
        if 'new_password' not in data and 'current_password' in data:
            raise serializers.ValidationError(_('New password must be supplied together with the current password'))

        if 'new_password' in data and 'current_password' not in data:
            raise serializers.ValidationError(_('Current password must be supplied together with the new password'))

        return data


class GetUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, user_username_exists],
                                     required=True)


class GetUserUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'location',
            'cover',
            'bio',
            'url'
        )


class GetUserUserSerializer(serializers.ModelSerializer):
    profile = GetUserUserProfileSerializer(many=False)
    followers_count = FollowersCountField()
    following_count = FollowingCountField()
    posts_count = PostsCountField()
    is_following = IsFollowingField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'followers_count',
            'following_count',
            'posts_count',
            'is_following',
            'is_connected'
        )


class GetUsersSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH, required=True)
    count = serializers.IntegerField(
        required=False,
        max_value=10
    )


class GetUsersUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'avatar',
            'name'
        )


class GetUsersUserSerializer(serializers.ModelSerializer):
    profile = GetUsersUserProfileSerializer(many=False)
    is_following = IsFollowingField()
    is_connected = IsConnectedField()

    class Meta:
        model = User
        fields = (
            'id',
            'profile',
            'username',
            'is_following',
            'is_connected'
        )
