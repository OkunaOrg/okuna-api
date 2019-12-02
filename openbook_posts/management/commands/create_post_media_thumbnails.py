from django.core.management.base import BaseCommand
import logging

from django.db import transaction
from django.db.models import Q

from openbook_common.utils.model_loaders import get_post_model, get_post_media_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates media_thumbnail, media_height and media_width for missing items'

    def handle(self, *args, **options):
        Post = get_post_model()
        PostMedia = get_post_media_model()

        logger.info(Post.objects.filter(media__isnull=False).count())

        posts_to_migrate = Post.objects.filter(Q(media__isnull=False) & Q(media_thumbnail__isnull=True))
        migrated_posts = 0

        for post in posts_to_migrate.iterator():
            with transaction.atomic():
                try:
                    post_first_media = post.get_first_media()
                    if post_first_media.type == PostMedia.MEDIA_TYPE_IMAGE:
                        post.media_width = post_first_media.content_object.width
                        post.media_height = post_first_media.content_object.height
                        post.media_thumbnail = post_first_media.content_object.image.file
                    elif post_first_media.type == PostMedia.MEDIA_TYPE_VIDEO:
                        post.media_width = post_first_media.content_object.width
                        post.media_height = post_first_media.content_object.height
                        post.media_thumbnail = post_first_media.content_object.thumbnail.file

                    post.save()
                except FileNotFoundError as e:
                    print('Ignoring post due to image not found')

            logger.info(post.media_width)
            logger.info(post.media_height)
            logger.info(post.media_thumbnail)

            migrated_posts = migrated_posts + 1

        logger.info('Created media_* for %d posts' % migrated_posts)
