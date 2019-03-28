from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from openbook_auth.models import User
from openbook_notifications.models.notification import Notification


class ConnectionRequestNotification(models.Model):
    notification = GenericRelation(Notification)
    connection_requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    @classmethod
    def create_connection_request_notification(cls, connection_requester_id, owner_id):
        connection_request_notification = cls.objects.create(connection_requester_id=connection_requester_id)
        Notification.create_notification(type=Notification.CONNECTION_REQUEST,
                                         content_object=connection_request_notification,
                                         owner_id=owner_id)
        return connection_request_notification

    @classmethod
    def delete_connection_request_notification_for_users_with_ids(cls, user_a_id, user_b_id):
        notification_query = Q(connection_requester_id=user_a_id, notification__owner_id=user_b_id)

        notification_query.add(Q(connection_requester_id=user_b_id, notification__owner_id=user_a_id), Q.OR)

        cls.objects.filter(notification_query).delete()


