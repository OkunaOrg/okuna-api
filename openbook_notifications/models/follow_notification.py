from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from openbook_auth.models import User
from openbook_notifications.models.notification import Notification


class FollowNotification(models.Model):
    notification = GenericRelation(Notification)
    follower = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def create_follow_notification(cls, follower_id, owner_id):
        follow_notification = cls.objects.create(follower_id=follower_id)
        return Notification.create_notification(type=Notification.FOLLOW,
                                                content_object=follow_notification,
                                                owner_id=owner_id)

    @classmethod
    def delete_follow_notification(cls, follower_id, owner_id):
        cls.objects.filter(follower_id=follower_id, notification__owner_id=owner_id).delete()


@receiver(pre_delete, sender=FollowNotification, dispatch_uid='follow_delete_cleanup')
def follow_notification_pre_delete(sender, instance, using, **kwargs):
    Notification.objects.filter(notification_type=Notification.FOLLOW, object_id=instance.pk).delete()
