from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_communities.models import Community


# Create your models here.
class Device(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', null=False)
    uuid = models.UUIDField(null=False, editable=False, unique=True)
    one_signal_player_id = models.CharField(_('one signal player id'), blank=False, null=True, max_length=255,
                                            unique=True)
    name = models.CharField(_('name'), max_length=settings.DEVICE_NAME_MAX_LENGTH, blank=False, null=True)
    notifications_enabled = models.BooleanField(_('notifications enabled'), default=True)
    created = models.DateTimeField(editable=False)

    @classmethod
    def create_device(cls, owner, uuid, name=None, one_signal_player_id=None,
                      notifications_enabled=None):
        device = cls.objects.create(owner=owner, uuid=uuid, name=name, one_signal_player_id=one_signal_player_id,
                                    notifications_enabled=notifications_enabled)

        return device

    def update(self, name=None, one_signal_player_id=None,
               notifications_enabled=None):
        if name:
            self.name = name

        if one_signal_player_id is not None:
            self.one_signal_player_id = one_signal_player_id

        if notifications_enabled is not None:
            self.notifications_enabled = notifications_enabled

        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Device, self).save(*args, **kwargs)
