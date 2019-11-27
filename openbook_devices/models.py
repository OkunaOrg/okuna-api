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
    uuid = models.CharField(_('uuid'), null=False, editable=False, unique=False,
                            max_length=settings.DEVICE_UUID_MAX_LENGTH)
    name = models.CharField(_('name'), max_length=settings.DEVICE_NAME_MAX_LENGTH, blank=False, null=True)
    created = models.DateTimeField(editable=False)

    class Meta:
        unique_together = ('owner', 'uuid',)

    @classmethod
    def create_device(cls, owner, uuid, name=None):
        device = cls.objects.create(owner=owner, uuid=uuid, name=name)

        return device

    def update(self, name=None):
        if name:
            self.name = name

        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Device, self).save(*args, **kwargs)
