from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

# Create your models here.
from openbook_notifications.models.notification import Notification
from openbook_posts.models import PostReaction


class PostReactionNotification(models.Model):
    notification = GenericRelation(Notification)
    post_reaction = models.ForeignKey(PostReaction, on_delete=models.CASCADE)

    @classmethod
    def create_post_reaction_notification(cls, post_reaction_id, owner_id):
        post_reaction_notification = cls.objects.create(post_reaction_id=post_reaction_id)
        notification = Notification.create_notification(type=Notification.POST_REACTION,
                                                        content_object=post_reaction_notification,
                                                        owner_id=owner_id)
        return notification
