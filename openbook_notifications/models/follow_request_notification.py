from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_follows.models import FollowRequest
from openbook_notifications.models.notification import Notification


class FollowRequestNotification(models.Model):
    notification = GenericRelation(Notification)
    follow_request = models.ForeignKey(FollowRequest, on_delete=models.CASCADE)

    @classmethod
    def create_follow__request_notification(cls, follow_request_id, owner_id):
        follow_request_notification = cls.objects.create(follow_request_id=follow_request_id)
        Notification.create_notification(type=Notification.FOLLOW_REQUEST,
                                         content_object=follow_request_notification,
                                         owner_id=owner_id)
        return follow_request_notification

    @classmethod
    def delete_follow__request_notification(cls, follow_request_id, owner_id):
        cls.objects.filter(follow_request_id=follow_request_id, notification__owner_id=owner_id).delete()
