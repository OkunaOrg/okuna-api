import re

from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def hex_color_validator(hex_color):
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_color):
        raise ValidationError(
            _('The provided value is not a valid hex color.'),
        )
