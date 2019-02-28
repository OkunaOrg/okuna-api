from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_auth.models import User
from openbook_notifications.models.notification import Notification


class ConnectionConfirmedNotification(models.Model):
    notification = GenericRelation(Notification)
    connection_confirmator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    @classmethod
    def create_connection_confirmed_notification(cls, connection_confirmator_id, owner_id):
        connection_confirmed_notification = cls.objects.create(connection_confirmator_id=connection_confirmator_id)
        notification = Notification.create_notification(type=Notification.CONNECTION_CONFIRMED,
                                                        content_object=connection_confirmed_notification,
                                                        owner_id=owner_id)
        return notification
