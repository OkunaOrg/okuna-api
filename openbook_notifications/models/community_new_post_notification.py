from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from openbook_communities.models import CommunityPostSubscription
from openbook_notifications.models.notification import Notification


class CommunityNewPostNotification(models.Model):
    notification = GenericRelation(Notification)
    community_post_subscription = models.ForeignKey(CommunityPostSubscription, on_delete=models.CASCADE)

    @classmethod
    def create_community_new_post_notification(cls, community_post_subscription_id, owner_id):
        community_post_subscription_notification = cls.objects.create(
            community_post_subscription=community_post_subscription_id)
        Notification.create_notification(type=Notification.COMMUNITY_NEW_POST,
                                         content_object=community_post_subscription_notification,
                                         owner_id=owner_id)
        return community_post_subscription_notification

    @classmethod
    def delete_community_new_post_notification(cls, community_post_subscription_id, owner_id):
        cls.objects.filter(community_post_subscription=community_post_subscription_id,
                           notification__owner_id=owner_id).delete()

