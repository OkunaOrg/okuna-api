from django.conf import settings
from django.db import models

# Create your models here.
from django.utils import timezone

from openbook.settings import CIRCLE_MAX_LENGTH, COLOR_ATTR_MAX_LENGTH
from openbook_auth.models import User
from openbook_common.utils.model_loaders import get_connection_model
from openbook_connections.models import Connection
from openbook_posts.models import Post
from openbook_common.validators import hex_color_validator
from django.utils.translation import ugettext_lazy as _


class ConnectionCircle(models.Model):
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE)

    class Meta:
        db_table = 'openbook_circles_circle_connections'
        unique_together = [
            ('connection', 'circle')
        ]
        indexes = [
            models.Index(fields=['connection', 'circle']),
        ]


class Circle(models.Model):
    creator = models.ForeignKey('openbook_auth.User', on_delete=models.CASCADE, related_name='circles', null=True)
    name = models.CharField(_('name'), max_length=CIRCLE_MAX_LENGTH, blank=False, null=False)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator])
    posts = models.ManyToManyField(Post, related_name='circles', db_index=True)
    connections = models.ManyToManyField(Connection, related_name='circles', db_index=True, through=ConnectionCircle)
    created = models.DateTimeField(editable=False)

    class Meta:
        unique_together = ('creator', 'name',)

    @classmethod
    def create_circle(cls, name, creator=None, color=None):
        circle = cls.objects.create(name=name, creator=creator, color=color, )
        return circle

    @classmethod
    def bootstrap_circles_for_user(cls, user):
        user_connections_circle = cls.create_circle(name=_('Connections'), color='#FFFFFF', creator=user)
        user.connections_circle = user_connections_circle
        user.save()

    @classmethod
    def is_name_taken_for_user(cls, name, user):
        try:
            cls.objects.get(creator=user, name=name)
            return True
        except Circle.DoesNotExist:
            return False

    @classmethod
    def get_world_circle(cls):
        return Circle.objects.get(pk=cls.get_world_circle_id())

    @classmethod
    def get_world_circle_id(cls):
        return settings.WORLD_CIRCLE_ID

    @property
    def users(self):
        Connection = get_connection_model()
        circle_connections = Connection.objects.select_related('target_connection__user').filter(
            circles__id=self.id)

        users = []
        for connection in circle_connections:
            users.append(connection.target_connection.user)

        return users

    @property
    def users_count(self):
        return Connection.objects.filter(
            circles__id=self.id).count()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Circle, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
