from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from openbook_auth.models import User


class Notification(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    created = models.DateTimeField(editable=False, db_index=True)
    read = models.BooleanField(default=False)

    POST_REACTION = 'PR'
    POST_COMMENT = 'PC'
    POST_COMMENT_REPLY = 'PCR'
    POST_COMMENT_REACTION = 'PCRA'
    CONNECTION_REQUEST = 'CR'
    CONNECTION_CONFIRMED = 'CC'
    FOLLOW = 'F'
    FOLLOW_REQUEST = 'FR'
    FOLLOW_REQUEST_APPROVED = 'FRA'
    COMMUNITY_INVITE = 'CI'
    POST_USER_MENTION = 'PUM'
    POST_COMMENT_USER_MENTION = 'PCUM'
    COMMUNITY_NEW_POST = 'CNP'
    USER_NEW_POST = 'UNP'

    NOTIFICATION_TYPES = (
        (POST_REACTION, 'Post Reaction'),
        (POST_COMMENT, 'Post Comment'),
        (POST_COMMENT_REPLY, 'Post Comment Reply'),
        (POST_COMMENT_REACTION, 'Post Comment Reaction'),
        (CONNECTION_REQUEST, 'Connection Request'),
        (CONNECTION_CONFIRMED, 'Connection Confirmed'),
        (FOLLOW, 'Follow'),
        (FOLLOW_REQUEST, 'Follow request'),
        (FOLLOW_REQUEST_APPROVED, 'Follow request approved'),
        (COMMUNITY_INVITE, 'Community Invite'),
        (POST_USER_MENTION, 'Post user mention'),
        (POST_COMMENT_USER_MENTION, 'Post comment user mention'),
        (COMMUNITY_NEW_POST, 'New post in community'),
        (USER_NEW_POST, 'New post by user'),
    )

    notification_type = models.CharField(max_length=5, choices=NOTIFICATION_TYPES)

    # Generic relation types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    @classmethod
    def create_notification(cls, owner_id, type, content_object):
        return cls.objects.create(notification_type=type, content_object=content_object, owner_id=owner_id)

    @classmethod
    def get_notification_types_values(cls):
        return [a for (a, b) in Notification.NOTIFICATION_TYPES]

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        return super(Notification, self).save(*args, **kwargs)
