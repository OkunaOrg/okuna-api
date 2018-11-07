from rest_framework import serializers

from openbook.settings import USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
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
    name = serializers.CharField(max_length=USERNAME_MAX_LENGTH, validators=[name_characters_validator],
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


class GetUserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'avatar',
            'birth_date'
        )


class GetUserSerializer(serializers.ModelSerializer):
    profile = GetUserProfileSerializer(many=False)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'profile',
            'posts_count',
            'followers_count'
        )
