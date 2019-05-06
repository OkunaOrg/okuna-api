from rest_framework.exceptions import ValidationError

from openbook_notifications.models import Notification
from django.utils.translation import gettext_lazy as _


def notification_id_exists(notification_id):
    if not Notification.objects.filter(pk=notification_id).exists():
        raise ValidationError(
            _('No notification with the provided id exists.'),
        )


def notification_type_exists(notification_type):
    matches = [a == notification_type for (a, b) in Notification.NOTIFICATION_TYPES]

    if not any(matches):
        raise ValidationError(
            _('The provided notification type is invalid.'),
        )