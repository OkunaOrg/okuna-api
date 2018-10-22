from rest_framework.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault
from django.utils.translation import ugettext_lazy as _

from openbook_circles.models import Circle


def circle_name_not_taken_for_user_validator(circle_name, user):
    if Circle.is_name_taken_for_user(circle_name, user):
        raise ValidationError(
            _('A circle with that name already exists.'),
        )
