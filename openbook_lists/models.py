from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_common.models import Emoji
from openbook_common.utils.model_loaders import get_follow_model
from openbook_follows.models import Follow


class List(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    emoji = models.ForeignKey(Emoji, on_delete=models.SET_NULL, related_name='lists', null=True)
    name = models.CharField(_('name'), max_length=settings.LIST_MAX_LENGTH, blank=False, null=False)
    follows = models.ManyToManyField(Follow, related_name='lists', db_index=True)
    created = models.DateTimeField(editable=False)

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
        Follow = get_follow_model()
        list_follows = Follow.objects.select_related('followed_user').filter(
            lists__id=self.id)
        users = []
        for follow in list_follows:
            users.append(follow.followed_user)
        return users

    def clear_users(self):
        follows = self.follows.all()
        for follow in follows:
            follow.lists.delete(self)

    @property
    def follows_count(self):
        return self.follows.count()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(List, self).save(*args, **kwargs)
