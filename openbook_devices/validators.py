from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_devices.models import Device


def device_id_exists(device_id):
    if not Device.objects.filter(id=device_id).exists():
        raise ValidationError(
            _('The device does not exist.'),
        )


def device_uuid_not_exists(device_uuid):
    if Device.objects.filter(uuid=device_uuid).exists():
        raise ValidationError(
            _('The uuid already exists.'),
        )
