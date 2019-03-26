from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

# Create your models here.
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from openbook_notifications.models.notification import Notification
from openbook_posts.models import PostReaction


class PostReactionNotification(models.Model):
    notification = GenericRelation(Notification)
    post_reaction = models.ForeignKey(PostReaction, on_delete=models.CASCADE)

    @classmethod
    def create_post_reaction_notification(cls, post_reaction_id, owner_id):
        post_reaction_notification = cls.objects.create(post_reaction_id=post_reaction_id)
        return Notification.create_notification(type=Notification.POST_REACTION,
                                                content_object=post_reaction_notification,
                                                owner_id=owner_id)

    @classmethod
    def delete_post_reaction_notification(cls, post_reaction_id, owner_id):
        cls.objects.filter(post_reaction_id=post_reaction_id,
                           notification__owner_id=owner_id).delete()



@receiver(pre_delete, sender=PostReactionNotification, dispatch_uid='post_reaction_delete_cleanup')
def post_reaction_notification_pre_delete(sender, instance, using, **kwargs):
    Notification.objects.filter(notification_type=Notification.POST_REACTION, object_id=instance.pk).delete()
