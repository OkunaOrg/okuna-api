from django.db import models

# Create your models here.
from openbook_auth.models import User


class Connection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    circle = models.ForeignKey('openbook_circles.Circle', on_delete=models.CASCADE, related_name='connections',
                               null=True)
    target_connection = models.OneToOneField('self', on_delete=models.CASCADE, null=True)

    @classmethod
    def create_connection(cls, user_id, target_user_id, **kwargs):
        target_connection = cls.objects.create(user_id=target_user_id)
        connection = cls.objects.create(user_id=user_id, target_connection=target_connection, **kwargs)
        # Why do we need to do this? Isn't it supposed to be default functionality
        # to add it to the other field too?
        target_connection.target_connection = connection
        target_connection.save()
        return connection

    @classmethod
    def connection_exists(cls, user_a_id, user_b_id):
        count = Connection.objects.select_related('target_connection__user_id').filter(user_id=user_a_id,
                                                                                       target_connection__user_id=user_b_id).count()
        return count > 0

    @classmethod
    def connection_exists_in_circle(cls, user_a_id, user_b_id, circle_id):
        count = Connection.objects.select_related('target_connection__user_id').filter(user_id=user_a_id,
                                                                                       target_connection__user_id=user_b_id,
                                                                                       circle_id=circle_id).count()
        return count > 0

    @classmethod
    def connection_exists_in_circles(cls, user_a_id, user_b_id, circles_ids):
        count = Connection.objects.select_related('target_connection__user_id').filter(user_id=user_a_id,
                                                                                       target_connection__user_id=user_b_id,
                                                                                       circle_id__in=circles_ids).count()
        return count == len(circles_ids)

    @classmethod
    def connection_with_id_exists_for_user_with_id(cls, connection_id, user_id):
        count = Connection.objects.filter(id=connection_id,
                                          user_id=user_id).count()
        if count > 0:
            return True

        return False

    @property
    def target_user(self):
        return self.target_connection.user
