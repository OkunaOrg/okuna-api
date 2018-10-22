from django.db import models

# Create your models here.
from openbook.settings import CIRCLE_MAX_LENGTH
from openbook_auth.models import User
from openbook_posts.models import COLOR_ATTR_MAX_LENGTH, Post
from openbook.validators import hex_color_validator
from django.utils.translation import ugettext_lazy as _


class Circle(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circles')
    name = models.CharField(_('name'), max_length=CIRCLE_MAX_LENGTH, blank=False, null=False)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    posts = models.ManyToManyField(Post, related_name='circles')
