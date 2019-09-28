from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_notifications.models.notification import Notification
from openbook_posts.models import PostUserMention


class PostUserMentionNotification(models.Model):
    notification = GenericRelation(Notification, related_name='post_user_mention_notifications')
    post_user_mention = models.ForeignKey(PostUserMention, on_delete=models.CASCADE)

    @classmethod
    def create_post_user_mention_notification(cls, post_user_mention_id, owner_id):
        post_user_mention_notification = cls.objects.create(post_user_mention_id=post_user_mention_id)
        Notification.create_notification(type=Notification.POST_USER_MENTION,
                                         content_object=post_user_mention_notification,
                                         owner_id=owner_id)
        return post_user_mention_notification

    @classmethod
    def delete_post_user_mention_notification(cls, post_user_mention_id, owner_id):
        cls.objects.filter(post_user_mention_id=post_user_mention_id,
                           notification__owner_id=owner_id).delete()
