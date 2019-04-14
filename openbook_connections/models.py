from django.db import models

# Create your models here.
from openbook_auth.models import User


class Connection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='targeted_connections', null=False)
    target_connection = models.OneToOneField('self', on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('user', 'target_user')
        index_together = [
            ('target_user', 'target_connection'),
            ('target_user', 'id'),
        ]

    @classmethod
    def create_connection(cls, user_id, target_user_id, circles_ids):
        target_connection = cls.objects.create(user_id=target_user_id, target_user_id=user_id)

        connection = cls.objects.create(user_id=user_id, target_user_id=target_user_id,
                                        target_connection=target_connection)

        connection.circles.add(*circles_ids)

        target_connection.target_connection = connection
        target_connection.save()

        connection.save()

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
                                                                                       circles__id=circle_id).count()
        return count > 0

    @classmethod
    def connection_exists_in_circles(cls, user_a_id, user_b_id, circles_ids):
        count = Connection.objects.select_related('target_connection__user_id').filter(user_id=user_a_id,
                                                                                       target_connection__user_id=user_b_id,
                                                                                       circles__id__in=circles_ids).count()
        return count == len(circles_ids)

    @classmethod
    def connection_with_id_exists_for_user_with_id(cls, connection_id, user_id):
        count = Connection.objects.filter(id=connection_id,
                                          user_id=user_id).count()
        if count > 0:
            return True

        return False
