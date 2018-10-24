from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_lists.models import List


def list_name_not_taken_for_user_validator(list_name, user):
    if List.is_name_taken_for_user(list_name, user):
        raise ValidationError(
            _('A list with that name already exists.'),
        )


def list_with_id_exists_for_user_with_id(list_id, user_id):
    return List.objects.filter(creator_id=user_id, id=list_id).count() > 0
