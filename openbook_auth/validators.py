import re
from django.conf import settings
import jwt
from django.utils.translation import gettext_lazy as _
from jwt import InvalidSignatureError
from jwt.exceptions import DecodeError, ExpiredSignatureError
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound

from openbook_auth.models import User


def username_characters_validator(username):
    if not re.match('^[a-zA-Z0-9_.]*$', username):
        raise ValidationError(
            _('Usernames can only contain alphanumeric characters, periods and underscores.'),
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


def user_username_exists(username):
    if not User.objects.filter(username=username).exists():
        raise NotFound(
            _('No user with the provided username exists.'),
        )


def user_email_exists(email):
    if not User.objects.filter(email=email).exists():
        raise NotFound(
            _('No user with the provided email exists.'),
        )


def is_of_legal_age_validator(is_confirmed):
    if is_confirmed is False:
        raise ValidationError(
            _('You must confirm you are over 16 years old to make an account'),
        )
