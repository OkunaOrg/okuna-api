from django.core.management.base import BaseCommand
import logging

from django.db.models import Q

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.jobs import _chunked_queryset_iterator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process the Posts\'s links'

    def handle(self, *args, **options):
        Post = get_post_model()

        text_query = Q(text__isnull=False,
                       text__icontains='http', )

        links_query = Q(links__isnull=True) | Q(links__has_preview=False)

        posts_to_process = Post.objects.filter(text_query & links_query).only('id', 'text').all()
        migrated_posts = 0

        for post in _chunked_queryset_iterator(posts_to_process, 100):
            try:
                post._process_post_links()
            except Exception as e:
                logger.info('Error processing with error %s' % str(e))
            logger.info('Processed links for post with id:' + str(post.pk))
            migrated_posts = migrated_posts + 1

        logger.info('Processed %d posts for links' % migrated_posts)
