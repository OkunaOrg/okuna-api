from django.db import models

# Create your models here.
from openbook.settings import CIRCLE_MAX_LENGTH
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_common.models import Emoji


class List(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    emoji = models.ForeignKey(Emoji, on_delete=models.SET_NULL, related_name='lists', null=True)
    name = models.CharField(_('name'), max_length=CIRCLE_MAX_LENGTH, blank=False, null=False)

