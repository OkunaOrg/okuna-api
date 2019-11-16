from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from openbook_auth.models import UserNotificationSubscription
from openbook_notifications.models.notification import Notification
from openbook_posts.models import Post


class UserNewPostNotification(models.Model):
    notification = GenericRelation(Notification)
    user_notification_subscription = models.ForeignKey(UserNotificationSubscription, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    @classmethod
    def create_user_new_post_notification(cls, user_notification_subscription_id, post_id, owner_id):
        user_new_post_notification = cls.objects.create(
            post_id=post_id,
            user_notification_subscription_id=user_notification_subscription_id)
        Notification.create_notification(type=Notification.USER_NEW_POST,
                                         content_object=user_new_post_notification,
                                         owner_id=owner_id)
        return user_new_post_notification

    @classmethod
    def delete_user_new_post_notification(cls, user_notification_subscription_id, post_id, owner_id):
        cls.objects.filter(user_notification_subscription_id=user_notification_subscription_id,
                           post_id=post_id,
                           notification__owner_id=owner_id).delete()

