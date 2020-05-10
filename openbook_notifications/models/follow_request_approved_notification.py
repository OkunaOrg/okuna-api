from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_follows.models import Follow
from openbook_notifications.models.notification import Notification


class FollowRequestApprovedNotification(models.Model):
    notification = GenericRelation(Notification)
    follow = models.ForeignKey(Follow, on_delete=models.CASCADE)

    @classmethod
    def create_follow_request_approved_notification(cls, follow_id, owner_id):
        follow_request_approved_notification = cls.objects.create(follow_id=follow_id)
        Notification.create_notification(type=Notification.FOLLOW_REQUEST_APPROVED,
                                         content_object=follow_request_approved_notification,
                                         owner_id=owner_id)
        return follow_request_approved_notification

    # No delete method because this will be auto-deleted when the follow is deleted.
    # Aka when a person unfollows the other person which created this approved notification.
