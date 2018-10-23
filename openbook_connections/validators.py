from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_connections.models import Connection


def connection_does_not_exist(user_a_id, user_b_id):
    if Connection.connection_exists(user_a_id, user_b_id):
        raise ValidationError(
            _('A connection already exists.'),
        )


def connection_with_id_exists_for_user_id(connection_id, user_id):
    if not Connection.connection_with_id_exists_for_user_with_id(connection_id, user_id):
        raise ValidationError(
            _('The connection does not exist.'),
        )
