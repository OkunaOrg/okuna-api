import re

from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_emoji_model, get_emoji_group_model, get_language_model


def is_valid_hex_color(hex_color):
    return re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_color)


def hex_color_validator(hex_color):
    if not is_valid_hex_color(hex_color):
        raise ValidationError(
            _('The provided value is not a valid hex color.'),
        )


def emoji_id_exists(list_id):
    Emoji = get_emoji_model()
    if not Emoji.objects.filter(pk=list_id).exists():
        raise ValidationError(
            _('No emoji with the provided id exists.'),
        )


def emoji_group_id_exists(emoji_group_id):
    EmojiGroup = get_emoji_group_model()
    if not EmojiGroup.objects.filter(pk=emoji_group_id).exists():
        raise ValidationError(
            _('No emoji group with the provided id exists.'),
        )


def name_characters_validator(name):
    if '>' in name or '<' in name:
        raise ValidationError(
            _('Names can\'t contain < or >.'),
        )


def language_id_exists(language_id):
    Language = get_language_model()
    if not Language.objects.filter(pk=language_id).exists():
        raise ValidationError(
            _('No supported language with the provided id exists.'),
        )


def language_code_exists(language_code):
    Language = get_language_model()
    if not Language.objects.filter(code=language_code).exists():
        raise ValidationError(
            _('No supported language with the provided code exists.'),
        )
