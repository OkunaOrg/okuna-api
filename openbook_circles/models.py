from django.db import models

# Create your models here.
from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import User
from openbook_posts.models import Post
from openbook_common.validators import hex_color_validator
from django.utils.translation import ugettext_lazy as _
from django.apps import apps


def get_connection_model():
    return apps.get_model('openbook_connections.Connection')


class Circle(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circles')
    name = models.CharField(_('name'), max_length=CIRCLE_MAX_LENGTH, blank=False, null=False)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    posts = models.ManyToManyField(Post, related_name='circles')

    class Meta:
        unique_together = ('creator', 'name',)

    @classmethod
    def is_name_taken_for_user(cls, name, user):
        try:
            cls.objects.get(creator=user, name=name)
            return True
        except Circle.DoesNotExist:
            return False

    @property
    def users(self):
        # TODO Optimize fetching
        circle_connections = get_connection_model().objects.select_related('target_connection').filter(circle_id=self.id)
        users = []
        for connection in circle_connections:
            users.append(connection.target_connection.user)
        return users
