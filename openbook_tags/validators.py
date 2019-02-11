from django.utils.translation import gettext_lazy as _

# Create your tests here.
from rest_framework.exceptions import ValidationError

from openbook_common.utils.model_loaders import get_tag_model


def tag_name_exists(tag_name):
    Tag = get_tag_model()
    if not Tag.objects.filter(name=tag_name).exists():
        raise ValidationError(
            _('No tag with the provided name exists.'),
        )
