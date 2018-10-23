from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_lists.models import List


def list_name_not_taken_for_user_validator(list_name, user):
    if List.is_name_taken_for_user(list_name, user):
        raise ValidationError(
            _('A list with that name already exists.'),
        )


def list_id_exists(list_id):
    try:
        List.objects.get(pk=list_id)
    except List.DoesNotExist:
        raise ValidationError(
            _('No list with the provided id exists.'),
        )
