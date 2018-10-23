from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_connections.models import Connection


def connection_does_not_exist(user_a, user_b):
    if Connection.connection_exists(user_a, user_b):
        raise ValidationError(
            _('A connection already exists.'),
        )
