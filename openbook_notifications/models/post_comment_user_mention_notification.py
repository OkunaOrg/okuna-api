from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from openbook_notifications.models.notification import Notification
from openbook_posts.models import PostCommentUserMention


class PostCommentUserMentionNotification(models.Model):
    notification = GenericRelation(Notification, related_name='post_comment_user_mention_notifications')
    post_comment_user_mention = models.ForeignKey(PostCommentUserMention, on_delete=models.CASCADE)

    @classmethod
    def create_post_comment_user_mention_notification(cls, post_comment_user_mention_id, owner_id):
        post_comment_user_mention_notification = cls.objects.create(
            post_comment_user_mention_id=post_comment_user_mention_id)
        Notification.create_notification(type=Notification.POST_COMMENT_USER_MENTION,
                                         content_object=post_comment_user_mention_notification,
                                         owner_id=owner_id)
        return post_comment_user_mention_notification

    @classmethod
    def delete_post_comment_user_mention_notification(cls, post_comment_user_mention_id, owner_id):
        cls.objects.filter(post_comment_user_mention_id=post_comment_user_mention_id,
                           notification__owner_id=owner_id).delete()
