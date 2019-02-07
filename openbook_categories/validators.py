from django.utils.translation import gettext_lazy as _

# Create your tests here.
from rest_framework.exceptions import ValidationError

from openbook_common.utils.model_loaders import get_category_model


def category_name_exists(category_name):
    Category = get_category_model()
    if not Category.objects.filter(name=category_name).exists():
        raise ValidationError(
            _('No category with the provided name exists.'),
        )
