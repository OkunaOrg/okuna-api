from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from openbook_auth.models import User
from openbook_communities.models import CommunityInvite
from openbook_notifications.models.notification import Notification


class CommunityInviteNotification(models.Model):
    notification = GenericRelation(Notification)
    community_invite = models.ForeignKey(CommunityInvite, on_delete=models.CASCADE)

    @classmethod
    def create_community_invite_notification(cls, community_invite_id, owner_id):
        community_invite_notification = cls.objects.create(community_invite_id=community_invite_id)
        return Notification.create_notification(type=Notification.COMMUNITY_INVITE,
                                                content_object=community_invite_notification,
                                                owner_id=owner_id)

    @classmethod
    def delete_community_invite_notification(cls, community_invite_id, owner_id):
        cls.objects.filter(community_invite_id=community_invite_id, notification__owner_id=owner_id).delete()


@receiver(pre_delete, sender=CommunityInviteNotification, dispatch_uid='community_invite_delete_cleanup')
def community_invite_notification_pre_delete(sender, instance, using, **kwargs):
    Notification.objects.filter(notification_type=Notification.COMMUNITY_INVITE, object_id=instance.pk).delete()
