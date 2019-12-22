from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from openbook_communities.models import CommunityNotificationsSubscription
from openbook_notifications.models.notification import Notification
from openbook_posts.models import Post


class CommunityNewPostNotification(models.Model):
    notification = GenericRelation(Notification)
    community_notifications_subscription = models.ForeignKey(CommunityNotificationsSubscription, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    @classmethod
    def create_community_new_post_notification(cls, community_notifications_subscription_id, post_id, owner_id):
        community_new_post_notification = cls.objects.create(
            post_id=post_id,
            community_notifications_subscription_id=community_notifications_subscription_id)
        Notification.create_notification(type=Notification.COMMUNITY_NEW_POST,
                                         content_object=community_new_post_notification,
                                         owner_id=owner_id)
        return community_new_post_notification

    @classmethod
    def delete_community_new_post_notification(cls, community_notifications_subscription_id, post_id, owner_id):
        cls.objects.filter(community_notifications_subscription_id=community_notifications_subscription_id,
                           post_id=post_id,
                           notification__owner_id=owner_id).delete()

