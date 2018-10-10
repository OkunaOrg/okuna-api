import re

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from openbook_auth.models import User


def username_characters_validator(username):
    if not re.match(r'^\w+$', username):
        raise ValidationError(
            _('Usernames can only contain alphanumeric characters and underscores.'),
        )


def name_characters_validator(name):
    if not re.match('(\w+\s\w+)', name):
        raise ValidationError(
            _('Names can only contain alphanumeric characters and spaces.'),
        )


def username_not_taken_validator(username):
    if User.is_username_taken(username):
        raise ValidationError(
            code=
            _('The username is already taken.')
        )


def email_not_taken_validator(email):
    if User.is_email_taken(email):
        raise ValidationError(
            _('An account for the email already exists.'),
        )
