from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_auth.models import User
from openbook_notifications.models.notification import Notification


class ConnectionRequestNotification(models.Model):
    notification = GenericRelation(Notification)
    connection_requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    @classmethod
    def create_connection_request_notification(cls, connection_requester_id, owner_id):
        connection_request_notification = cls.objects.create(connection_requester_id=connection_requester_id)
        notification = Notification.create_notification(type=Notification.CONNECTION_REQUEST,
                                                        content_object=connection_request_notification,
                                                        owner_id=owner_id)
        return notification

    @classmethod
    def remove_connection_request_notification(cls, connection_requester_id, owner_id):
        cls.objects.filter(connection_requester_id=connection_requester_id, notification__owner_id=owner_id).delete()
