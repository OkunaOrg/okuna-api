# Create your models here.
# Create your models here.
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from openbook.settings import COLOR_ATTR_MAX_LENGTH
from openbook_common.validators import hex_color_validator


class EmojiGroup(models.Model):
    keyword = models.CharField(_('keyword'), max_length=32, blank=False, null=False)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator], unique=False)
    order = models.IntegerField(unique=False, default=100)
    created = models.DateTimeField(editable=False)
    is_reaction_group = models.BooleanField(_('is reaction group'), default=False)

    def __str__(self):
        return 'EmojiGroup: ' + self.keyword

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(EmojiGroup, self).save(*args, **kwargs)

    def has_emoji_with_id(self, emoji_id):
        return self.emojis.filter(pk=emoji_id).exists()


class Emoji(models.Model):
    group = models.ForeignKey(EmojiGroup, on_delete=models.CASCADE, related_name='emojis', null=True)
    keyword = models.CharField(_('keyword'), max_length=16, blank=False, null=False)
    # Hex colour. #FFFFFF
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator], unique=False)
    image = models.ImageField(_('image'), blank=False, null=False, unique=True)
    created = models.DateTimeField(editable=False)
    order = models.IntegerField(unique=False, default=100)

    def __str__(self):
        return 'Emoji: ' + self.keyword

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Emoji, self).save(*args, **kwargs)


class Badge(models.Model):
    keyword = models.CharField(max_length=16, blank=False, null=False, unique=True)
    keyword_description = models.CharField(_('keyword_description'), max_length=64, blank=True, null=True, unique=True)
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Badge, self).save(*args, **kwargs)
