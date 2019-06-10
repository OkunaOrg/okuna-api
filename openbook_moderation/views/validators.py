from rest_framework.exceptions import NotFound

from openbook_moderation.models import ModerationCategory, ModeratedObject
from django.utils.translation import ugettext_lazy as _


def moderation_category_id_exists(moderation_category_id):
    if not ModerationCategory.objects.filter(id=moderation_category_id).exists():
        raise NotFound(
            _('The category does not exist.'),
        )


def moderated_object_id_exists(moderated_object_id):
    if not ModeratedObject.objects.filter(id=moderated_object_id).exists():
        raise NotFound(
            _('The moderated object does not exist.'),
        )
