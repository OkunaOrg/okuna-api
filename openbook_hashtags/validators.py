from rest_framework.exceptions import NotFound
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.helpers import hashtags_regexp
from openbook_common.utils.model_loaders import get_hashtag_model


def hashtag_name_exists(hashtag_name):
    Hashtag = get_hashtag_model()
    if not Hashtag.hashtag_with_name_exists(hashtag_name=hashtag_name):
        raise NotFound(
            _('No hashtag with the provided name exists.'),
        )


def hashtag_name_validator(hashtag_name):
    if not hashtags_regexp.match('#%s' % hashtag_name):
        raise NotFound(
            _('Hashtags must to be alphanumerical and up to 32 characters.'),
        )
