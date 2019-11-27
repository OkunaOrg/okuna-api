from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_categories.models import Category
from openbook_common.utils.helpers import generate_random_hex_color
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community


class Hashtag(models.Model):
    name = models.CharField(_('name'), max_length=settings.HASHTAG_NAME_MAX_LENGTH, blank=False, null=False,
                            unique=True)
    color = models.CharField(_('color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    created = models.DateTimeField(editable=False)
    posts = models.ManyToManyField(Community, related_name='hashtags')

    @classmethod
    def create_hashtag(cls, name, color=None):
        if not color:
            color = generate_random_hex_color()

        name = name.lower()
        tag = cls.objects.create(name=name, color=color, description=None)

        return tag

    @classmethod
    def get_or_create_hashtag_with_name(cls, name):
        try:
            hashtag = cls.objects.get(name=name)
        except cls.DoesNotExist:
            hashtag = cls.create_hashtag(name=name)

        return hashtag

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Hashtag, self).save(*args, **kwargs)
