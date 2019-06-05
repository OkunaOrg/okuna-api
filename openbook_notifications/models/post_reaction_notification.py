from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from openbook_notifications.models.notification import Notification
from openbook_posts.models import PostReaction


class PostReactionNotification(models.Model):
    notification = GenericRelation(Notification, related_name='post_reaction_notifications')
    post_reaction = models.ForeignKey(PostReaction, on_delete=models.CASCADE)

    @classmethod
    def create_post_reaction_notification(cls, post_reaction_id, owner_id):
        post_reaction_notification = cls.objects.create(post_reaction_id=post_reaction_id)
        Notification.create_notification(type=Notification.POST_REACTION,
                                         content_object=post_reaction_notification,
                                         owner_id=owner_id)
        return post_reaction_notification

    @classmethod
    def delete_post_reaction_notification(cls, post_reaction_id, owner_id):
        cls.objects.filter(post_reaction_id=post_reaction_id,
                           notification__owner_id=owner_id).delete()

    @classmethod
    def delete_post_reaction_notifications(cls, post_reaction_id):
        cls.objects.filter(post_reaction_id=post_reaction_id).delete()
