from django.apps import apps
from django.db import models

# Create your models here.
from openbook.settings import CIRCLE_MAX_LENGTH
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_common.models import Emoji


def get_follow_model():
    return apps.get_model('openbook_follows.Follow')


class List(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    emoji = models.ForeignKey(Emoji, on_delete=models.SET_NULL, related_name='lists', null=True)
    name = models.CharField(_('name'), max_length=CIRCLE_MAX_LENGTH, blank=False, null=False)

    class Meta:
        unique_together = ('creator', 'name',)

    @classmethod
    def is_name_taken_for_user(cls, name, user):
        try:
            cls.objects.get(creator=user, name=name)
            return True
        except List.DoesNotExist:
            return False

    @property
    def users(self):
        list_follows = get_follow_model().objects.select_related('followed_user').filter(
            list_id=self.id)
        users = []
        for follow in list_follows:
            users.append(follow.followed_user)
        return users
