from django.apps import apps
from django.db import models

# Create your models here.
from openbook_auth.models import User


def get_follow_model():
    return apps.get_model('openbook_follows.Follow')


class Connection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE, related_name='connections',
                               null=True)
    target_connection = models.OneToOneField('self', on_delete=models.CASCADE, null=True)

    @classmethod
    def create_connection(cls, user_id, target_user_id, circle_id):
        target_connection = cls.objects.create(user_id=target_user_id)
        connection = cls.objects.create(user_id=user_id, target_connection=target_connection, circle_id=circle_id)
        # Why do we need to do this? Isn't it supposed to be default functionality
        # to add it to the other field too?
        target_connection.target_connection = connection
        target_connection.save()

        # Follow the user if not already following
        Follow = get_follow_model()

        if not Follow.follow_exists(user_id, target_user_id):
            Follow.create_follow(user_id=user_id, followed_user_id=target_user_id)

        return connection

    @classmethod
    def connection_exists(cls, user_a, user_b):
        count = user_a.connections.filter(target_connection__user=user_b.pk).count()
        if count > 0:
            return True

        return False

    @classmethod
    def connection_with_id_exists_for_user(cls, connection_id, user):
        count = user.connections.filter(pk=connection_id).count()

        if count > 0:
            return True

        return False

    @property
    def target_user(self):
        return self.target_connection.user
