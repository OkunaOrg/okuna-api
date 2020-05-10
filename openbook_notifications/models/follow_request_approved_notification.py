from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_auth.models import User
from openbook_follows.models import FollowRequest
from openbook_notifications.models.notification import Notification


class FollowRequestApprovedNotification(models.Model):
    notification = GenericRelation(Notification)
    approver = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def create_follow__request_approved_notification(cls, approver_id, owner_id):
        follow_request_approved_notification = cls.objects.create(approver_id=approver_id)
        Notification.create_notification(type=Notification.FOLLOW_REQUEST_APPROVED,
                                         content_object=follow_request_approved_notification,
                                         owner_id=owner_id)
        return follow_request_approved_notification

    @classmethod
    def delete_follow__request_approved_notification(cls, approver_id, owner_id):
        cls.objects.filter(approver_id=approver_id, notification__owner_id=owner_id).delete()
