import re

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from openbook_communities.models import Community


def community_name_characters_validator(community_name):
    if not re.match('^[a-zA-Z0-9_]*$', community_name):
        raise ValidationError(
            _('Community_names can only contain alphanumeric characters, underscores and dashes.'),
        )


def community_name_not_taken_validator(community_name):
    if Community.is_name_taken(community_name):
        raise ValidationError(
            _('Community name already taken.'),
        )


def community_name_exists(community_name):
    if not Community.objects.filter(name=community_name).exists():
        raise ValidationError(
            _('No community with the provided name exists.'),
        )
