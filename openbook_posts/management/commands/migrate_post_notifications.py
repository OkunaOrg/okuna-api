from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.helpers import chunked_queryset_iterator
from openbook_common.utils.model_loaders import get_post_model, get_post_notifications_subscription_model, \
    get_post_comment_model, get_post_comment_notifications_subscription_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates PostNotificationsSubscription and ' \
           'PostCommentNotificationsSubscription objects for each post/comment'

    def handle(self, *args, **options):
        Post = get_post_model()
        PostComment = get_post_comment_model()

        posts_to_migrate = Post.objects.only('id', 'creator').all()
        migrated_posts = 0

        for post in chunked_queryset_iterator(posts_to_migrate, 1000):
            post_comments = PostComment.objects.select_related('post', 'commenter', 'parent_comment').\
                filter(post=post)
            with transaction.atomic():
                self.create_notifications_subscription_for_creator(post)
                for comment in post_comments:
                    if comment.parent_comment is None:
                        self.create_notifications_subscription_for_commenter(comment)
                    else:
                        # reply
                        self.create_notifications_subscription_for_replier(comment)

                migrated_posts = migrated_posts + 1

        logger.info('Migrated %d posts' % migrated_posts)

    def create_notifications_subscription_for_creator(self, post):
        PostNotificationsSubscription = get_post_notifications_subscription_model()
        PostNotificationsSubscription.get_or_create_post_notifications_subscription(
            post=post,
            subscriber=post.creator,
            comment_notifications=True,
            reaction_notifications=True,
            reply_notifications=False)

    def create_notifications_subscription_for_commenter(self, post_comment):
        # notification subscription for post
        PostNotificationsSubscription = get_post_notifications_subscription_model()
        PostNotificationsSubscription.get_or_create_post_notifications_subscription(
            post=post_comment.post,
            subscriber=post_comment.commenter,
            comment_notifications=True,
            reaction_notifications=False,
            reply_notifications=False)
        # notification subscription for comment
        PostCommentNotificationsSubscription = get_post_comment_notifications_subscription_model()
        PostCommentNotificationsSubscription.get_or_create_post_comment_notifications_subscription(
            post_comment=post_comment,
            subscriber=post_comment.commenter,
            reaction_notifications=True,
            reply_notifications=True
        )

    def create_notifications_subscription_for_replier(self, post_comment_reply):
        # notification subscription for post
        PostNotificationsSubscription = get_post_notifications_subscription_model()
        PostNotificationsSubscription.get_or_create_post_notifications_subscription(
            post=post_comment_reply.post,
            subscriber=post_comment_reply.commenter,
            comment_notifications=False,
            reaction_notifications=False,
            reply_notifications=False)
        # notification subscription for parent comment
        PostCommentNotificationsSubscription = get_post_comment_notifications_subscription_model()
        PostCommentNotificationsSubscription.get_or_create_post_comment_notifications_subscription(
            post_comment=post_comment_reply.parent_comment,
            subscriber=post_comment_reply.commenter,
            reaction_notifications=False,
            reply_notifications=True
        )
        # notification subscription for reply
        PostCommentNotificationsSubscription = get_post_comment_notifications_subscription_model()
        PostCommentNotificationsSubscription.get_or_create_post_comment_notifications_subscription(
            post_comment=post_comment_reply,
            subscriber=post_comment_reply.commenter,
            reaction_notifications=True,
            reply_notifications=True
        )
