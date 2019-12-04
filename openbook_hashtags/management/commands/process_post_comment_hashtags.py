from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.model_loaders import get_post_comment_model
from openbook_posts.jobs import _chunked_queryset_iterator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process the PostComments\'s hashtags'

    def handle(self, *args, **options):
        PostComment = get_post_comment_model()

        comments_to_process = PostComment.objects.filter(hashtags__isnull=True,
                                                         text__icontains='#').only('id', 'text').all()
        migrated_postComments = 0

        for comment in _chunked_queryset_iterator(comments_to_process, 100):
            try:
                comment._process_post_comment_hashtags()
            except Exception as e:
                logger.info('Failed to process hashtags with error %s' % str(e))
            logger.info('Processed hashtags for post comment with id:' + str(comment.pk))
            migrated_postComments = migrated_postComments + 1

        logger.info('Processed %d post comments for hashtags' % migrated_postComments)
