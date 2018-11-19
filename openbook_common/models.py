# Create your models here.
# Create your models here.
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from openbook.settings import COLOR_ATTR_MAX_LENGTH
from openbook_common.validators import hex_color_validator


class Emoji(models.Model):
    keyword = models.CharField(_('keyword'), max_length=16, blank=False, null=False, unique=True)
    # Hex colour. #FFFFFF
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator], unique=False)
    image = models.ImageField(_('image'), blank=False, null=False, unique=True)
    created = models.DateTimeField(editable=False)
    order = models.IntegerField(unique=False, default=100)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Emoji, self).save(*args, **kwargs)
