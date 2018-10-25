from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_circles.models import Circle


def circle_name_not_taken_for_user_validator(circle_name, user):
    if Circle.is_name_taken_for_user(circle_name, user):
        raise ValidationError(
            _('A circle with that name already exists.'),
        )


def circle_id_exists(circle_id):
    count = Circle.objects.filter(id=circle_id).count()

    if count == 0:
        raise ValidationError(
            _('The circle does not exist.'),
        )
