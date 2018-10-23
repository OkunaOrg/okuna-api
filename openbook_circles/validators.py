from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_circles.models import Circle


def circle_name_not_taken_for_user_validator(circle_name, user):
    if Circle.is_name_taken_for_user(circle_name, user):
        raise ValidationError(
            _('A circle with that name already exists.'),
        )


def circle_id_exists(circle_id):
    try:
        Circle.objects.get(pk=circle_id)
    except Circle.DoesNotExist:
        raise ValidationError(
            _('No circle with the provided id exists.'),
        )
