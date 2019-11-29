import re

from rest_framework.exceptions import NotFound
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_hashtag_model


def hashtag_name_exists(hashtag_name):
    Hashtag = get_hashtag_model()
    if not Hashtag.hashtag_with_name_exists(hashtag_name=hashtag_name):
        raise NotFound(
            _('No hashtag with the provided name exists.'),
        )


hashtag_name_regexp = re.compile('[a-zA-Z]+')


def hashtag_name_validator(hashtag_name):
    return hashtag_name_regexp.match(hashtag_name)
