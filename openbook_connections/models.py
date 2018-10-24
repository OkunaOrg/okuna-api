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
    def connection_with_id_exists_for_user_with_id(cls, connection_id, user_id):
        count = Connection.objects.filter(id=connection_id,
                                          user_id=user_id).count()
        if count > 0:
            return True

        return False

    @property
    def target_user(self):
        return self.target_connection.user

    def delete(self, *args, **kwargs):
        user_id = self.user_id
        target_user_id = self.target_connection.user_id

        # Unfollow the user if following
        Follow = get_follow_model()
        if Follow.follow_exists(user_id, target_user_id):
            Follow.delete_follow(user_id, target_user_id)

        return super(Connection, self).delete(*args, **kwargs)
