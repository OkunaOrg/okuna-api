from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_circles.models import Circle


def circle_name_not_taken_for_user_validator(circle_name, user):
    if Circle.is_name_taken_for_user(circle_name, user):
        raise ValidationError(
            _('A circle with that name already exists.'),
        )


def circle_with_id_exists_for_user_with_id(circle_id, user_id):
    count = Circle.objects.filter(creator_id=user_id, id=circle_id).count()

    if count == 0:
        raise ValidationError(
            _('No circle for user exists.'),
        )
