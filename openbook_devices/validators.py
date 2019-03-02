from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from openbook_devices.models import Device


def device_id_exists(device_id):
    if Device.objects.filter(id=device_id).count() == 0:
        raise ValidationError(
            _('The device does not exist.'),
        )
