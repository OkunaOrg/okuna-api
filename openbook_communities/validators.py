import re

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from openbook_auth.models import User


def community_name_characters_validator(community_name):
    if not re.match('^[a-zA-Z0-9_]*$', community_name):
        raise ValidationError(
            _('Community_names can only contain alphanumeric characters and underscores.'),
        )


def community_name_not_taken_validator(community_name):
    if User.is_community_name_taken(community_name):
        raise ValidationError(
            _('The community_name is already taken.'),
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


def user_community_name_exists(community_name):
    count = User.objects.filter(community_name=community_name).count()
    if count == 0:
        raise ValidationError(
            _('No user with the provided community_name exists.'),
        )
