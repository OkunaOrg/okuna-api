import re

from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_emoji_model


def hex_color_validator(hex_color):
    if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_color):
        raise ValidationError(
            _('The provided value is not a valid hex color.'),
        )


def emoji_id_exists(list_id):
    Emoji = get_emoji_model()
    try:
        Emoji.objects.get(pk=list_id)
    except Emoji.DoesNotExist:
        raise ValidationError(
            _('No emoji with the provided id exists.'),
        )


def name_characters_validator(name):
    if '>' in name or '<' in name:
        raise ValidationError(
            _('Names cant contain < or >.'),
        )
