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


class Tag(models.Model):
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_tags', null=True)
    name = models.CharField(_('name'), max_length=settings.TAG_NAME_MAX_LENGTH, blank=False, null=False, unique=True)
    color = models.CharField(_('color'), max_length=settings.COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    created = models.DateTimeField(editable=False)
    categories = models.ManyToManyField(Category, related_name='tags')
    posts = models.ManyToManyField(Community, related_name='tags')

    @classmethod
    def create_tag(cls, creator, name, color=None):

        if not color:
            color = generate_random_hex_color()

        tag = cls.objects.create(creator=creator, name=name, color=color, description=None)

        return tag

    @classmethod
    def get_tags_with_names_for_user(cls, tags_names, user):
        existing_tags = cls.objects.filter(name__in=tags_names).all()
        existing_tags_names = [tag.pk for tag in existing_tags]

        for tag_name in tags_names:
            if tag_name not in existing_tags_names:
                new_tag = cls.create_tag(creator=user, name=tag_name)
                existing_tags.append(new_tag)

        return existing_tags

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Tag, self).save(*args, **kwargs)
