from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

# Create your models here.
from openbook_auth.models import User
from openbook_notifications.models.notification import Notification


class FollowNotification(models.Model):
    notification = GenericRelation(Notification)
    follower = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def create_follow_notification(cls, follower_id, owner_id):
        follow_notification = cls.objects.create(follower_id=follower_id)
        notification = Notification.create_notification(type=Notification.FOLLOW,
                                                        content_object=follow_notification,
                                                        owner_id=owner_id)
        return notification
