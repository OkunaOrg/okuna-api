from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.jobs import _chunked_queryset_iterator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process the Posts\'s hashtags'

    def handle(self, *args, **options):
        Post = get_post_model()

        posts_to_process = Post.objects.filter(hashtags__isnull=True, text__isnull=False).all()
        migrated_posts = 0

        for post in _chunked_queryset_iterator(posts_to_process, 1000):
            with transaction.atomic():
                post._process_post_hashtags()
            logger.info('Processed hashtags for post with id:' + str(post.pk))
            migrated_posts = migrated_posts + 1

        logger.info('Processed %d posts for hashtags' % migrated_posts)
