from rest_framework.exceptions import ValidationError

from openbook_notifications.models import Notification
from django.utils.translation import gettext_lazy as _


def notification_id_exists(notification_id):
    if not Notification.objects.filter(pk=notification_id).exists():
        raise ValidationError(
            _('No notification with the provided id exists.'),
        )
