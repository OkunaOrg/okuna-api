from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community


class Tag(models.Model):
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_tags', null=True)
    name = models.CharField(_('name'), max_length=settings.TAG_MAX_LENGTH, blank=False, null=False, unique=False)
    title = models.CharField(_('title'), max_length=settings.TAG_TITLE_MAX_LENGTH, blank=False, null=False)
    description = models.CharField(_('description'), max_length=settings.TAG_DESCRIPTION_MAX_LENGTH, blank=False,
                                   null=True, )
    verified = models.BooleanField(_('verified'), default=False)
    color = models.CharField(_('color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    created = models.DateTimeField(editable=False)
    communities = models.ManyToManyField(Community, related_name='communities')
    posts = models.ManyToManyField(Community, related_name='posts')

    @classmethod
    def create_tag(cls, creator, name, color):
        tag = cls.objects.create(creator=creator, name=name, color=color)
        return tag

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Tag, self).save(*args, **kwargs)
