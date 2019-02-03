import re

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


def community_name_characters_validator(community_name):
    if not re.match('^[a-zA-Z0-9_]*$', community_name):
        raise ValidationError(
            _('Community_names can only contain alphanumeric characters, underscores and dashes.'),
        )
