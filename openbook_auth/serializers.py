from rest_framework import serializers

from openbook_auth.validators import username_characters_validator, name_characters_validator, \
    username_not_taken_validator, email_not_taken_validator
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=100, validators=[validate_password])
    birth_date = serializers.DateField(input_formats=["%d-%m-%Y"])
    username = serializers.CharField(min_length=1, max_length=30,
                                     validators=[username_characters_validator, username_not_taken_validator])
    name = serializers.CharField(min_length=1, max_length=50, validators=[name_characters_validator])
    avatar = serializers.FileField(allow_empty_file=True, required=False)
    email = serializers.EmailField(validators=[email_not_taken_validator])


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=1, max_length=30,
                                     validators=[username_characters_validator, username_not_taken_validator])


class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_not_taken_validator])


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=1, max_length=30,
                                     validators=[username_characters_validator])
    password = serializers.CharField(min_length=8, max_length=100)
