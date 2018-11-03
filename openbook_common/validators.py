import re

from django.apps import apps
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def get_emoji_model():
    return apps.get_model('openbook_common.Emoji')


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
