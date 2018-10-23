from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_follows.models import Follow


def follow_does_not_exist(user_a_id, user_b_id):
    if Follow.follow_exists(user_a_id, user_b_id):
        raise ValidationError(
            _('A follow already exists.'),
        )


def follow_with_id_exists_for_user(follow_id, user):
    if not Follow.follow_with_id_exists_for_user(follow_id, user):
        raise ValidationError(
            _('The follow does not exist.'),
        )
