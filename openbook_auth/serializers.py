from rest_framework import serializers
from django.conf import settings

from openbook.settings import USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, PROFILE_NAME_MAX_LENGTH
from openbook_auth.models import User, UserProfile
from openbook_auth.validators import username_characters_validator, name_characters_validator, \
    username_not_taken_validator, email_not_taken_validator
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password])
    birth_date = serializers.DateField(input_formats=["%d-%m-%Y"])
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     validators=[username_characters_validator, username_not_taken_validator],
                                     allow_blank=False)
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH, validators=[name_characters_validator],
                                 allow_blank=False)
    avatar = serializers.ImageField(allow_empty_file=True, required=False)
    email = serializers.EmailField(validators=[email_not_taken_validator])


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator, username_not_taken_validator])


class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_not_taken_validator])


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
            'location',
            'cover',
            'birth_date',
            'followers_count_visible'
        )


class GetAuthenticatedUserSerializer(serializers.ModelSerializer):
    profile = GetAuthenticatedUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'profile',
            'posts_count',
            'followers_count'
        )


class UpdateAuthenticatedUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=USERNAME_MAX_LENGTH,
                                     allow_blank=False,
                                     validators=[username_characters_validator],
                                     required=False)
    avatar = serializers.ImageField(allow_empty_file=False, required=False, allow_null=False)
    cover = serializers.ImageField(allow_empty_file=False, required=False, allow_null=False)
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH,
                                     validators=[validate_password], required=False, allow_blank=False)
    birth_date = serializers.DateField(input_formats=["%d-%m-%Y"], required=False, allow_null=False)
    name = serializers.CharField(max_length=PROFILE_NAME_MAX_LENGTH, validators=[name_characters_validator],
                                 required=False,
                                 allow_blank=False)
    followers_count_visible = serializers.BooleanField(required=False, default=None, allow_null=True)
    bio = serializers.CharField(max_length=settings.PROFILE_BIO_MAX_LENGTH, required=False,
                                allow_blank=False)
    location = serializers.CharField(max_length=settings.PROFILE_LOCATION_MAX_LENGTH, required=False,
                                     allow_blank=False)


class GetUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'name',
            'avatar',
            'location',
            'cover',
            'bio',
        )


class GetUserSerializer(serializers.ModelSerializer):
    profile = GetUserProfileSerializer(many=False)
    followers_count = serializers.SerializerMethodField()

    def get_followers_count(self, obj):
        if obj.profile.followers_count_visible:
            return obj.followers_count
        return None

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile',
            'followers_count'
        )
