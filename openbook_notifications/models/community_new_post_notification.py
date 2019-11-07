from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from openbook_auth.models import User
from openbook_communities.models import CommunityNotificationSubscription
from openbook_notifications.models.notification import Notification


class CommunityNewPostNotification(models.Model):
    notification = GenericRelation(Notification)
    community_notification_subscription = models.ForeignKey(CommunityNotificationSubscription, on_delete=models.CASCADE)

    @classmethod
    def create_community_new_post_notification(cls, community_notification_subscription_id, owner_id):
        community_new_post_notification = cls.objects.create(
            community_notification_subscription_id=community_notification_subscription_id)
        Notification.create_notification(type=Notification.COMMUNITY_NEW_POST,
                                         content_object=community_new_post_notification,
                                         owner_id=owner_id)
        return community_new_post_notification

    @classmethod
    def delete_community_new_post_notification(cls, community_notification_subscription_id, owner_id):
        cls.objects.filter(community_notification_subscription_id=community_notification_subscription_id,
                           notification__owner_id=owner_id).delete()

