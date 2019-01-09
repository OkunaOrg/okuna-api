import re
from django.conf import settings
import jwt
from django.utils.translation import gettext_lazy as _
from jwt import InvalidSignatureError
from jwt.exceptions import DecodeError
from rest_framework.exceptions import ValidationError, AuthenticationFailed

from openbook_auth.models import User


def username_characters_validator(username):
    if not re.match('^[a-zA-Z0-9_]*$', username):
        raise ValidationError(
            _('Usernames can only contain alphanumeric characters and underscores.'),
        )


def username_not_taken_validator(username):
    if User.is_username_taken(username):
        raise ValidationError(
            _('The username is already taken.'),
        )


def email_not_taken_validator(email):
    if User.is_email_taken(email):
        raise ValidationError(
            _('An account for the email already exists.'),
        )


def user_id_exists(user_id):
    try:
        User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValidationError(
            _('No user with the provided id exists.'),
        )


def user_username_exists(username):
    count = User.objects.filter(username=username).count()
    if count == 0:
        raise ValidationError(
            _('No user with the provided username exists.'),
        )


def jwt_token_validator(token):
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except InvalidSignatureError:
        raise AuthenticationFailed(
            _('Token is invalid.'),
        )
    except DecodeError:
        raise AuthenticationFailed(
            _('Token is invalid.'),
        )


def is_of_legal_age_validator(is_confirmed):
    if is_confirmed is False:
        raise ValidationError(
            _('You must confirm you are over 16 years old to make an account'),
        )