from django.db import models

# Create your models here.
from openbook_auth.models import User


class Connection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE, related_name='connections',
                               null=True)
    target_connection = models.OneToOneField('self', on_delete=models.CASCADE, null=True)

    @classmethod
    def create_connection(cls, user, target_user_id, circle_id):
        target_connection = cls.objects.create(user_id=target_user_id)
        connection = cls.objects.create(user=user, target_connection=target_connection, circle_id=circle_id)
        # Why do we need to do this? Isn't it supposed to be default functionality
        # to add it to the other field too?
        target_connection.target_connection = connection
        target_connection.save()
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
