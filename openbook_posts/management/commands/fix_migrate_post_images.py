from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.model_loaders import get_post_model
from openbook_posts.models import PostImage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fixed migrates the Post.image\'s to PostMedia items'

    def handle(self, *args, **options):
        Post = get_post_model()

        posts_to_migrate = Post.objects.filter(image__isnull=True, media__isnull=False)
        migrated_posts = 0

        for post in posts_to_migrate.iterator():
            with transaction.atomic():
                post_image = post.get_first_media().content_object
                if isinstance(post_image, PostImage):
                    post_image.post = post
                    post_image.save()
                    logger.info('Fixed migrated post with id:' + str(post.pk))
            migrated_posts = migrated_posts + 1

        logger.info('Fixed migrated %d posts' % migrated_posts)
