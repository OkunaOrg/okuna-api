import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def username_characters_validator(username):
    if not re.match(r'^\w+$', username):
        raise ValidationError(
            _('%(value)s can only contain alphanumeric characters and underscores.'),
            params={'value': username},
        )


def name_characters_validator(name):
    if not re.match('(\w+\s\w+)', name):
        raise ValidationError(
            _('%(value)s can only contain alphanumeric characters and spaces.'),
            params={'value': name},
        )
