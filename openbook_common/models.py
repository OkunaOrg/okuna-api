
# Create your models here.
# Create your models here.
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from openbook_common.validators import hex_color_validator

# #FFFFFF
COLOR_ATTR_MAX_LENGTH = 7


class Emoji(models.Model):
    name = models.CharField(_('name'), max_length=32, blank=False, null=False)
    shortcut = models.CharField(_('shortcut'), max_length=16, blank=False, null=False)
    # Hex colour. #FFFFFF
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    image = models.ImageField(_('image'), blank=False, null=False)
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Emoji, self).save(*args, **kwargs)
