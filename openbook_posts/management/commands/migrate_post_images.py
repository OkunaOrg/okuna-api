from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.model_loaders import  get_post_model, get_post_media_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrates the Post.image\'s to PostMedia items'

    def handle(self, *args, **options):
        Post = get_post_model()
        PostMedia = get_post_media_model()

        posts_to_migrate = Post.objects.filter(image__isnull=False, media__isnull=True)
        migrated_posts = 0

        for post in posts_to_migrate.iterator():
            with transaction.atomic():
                post_image = post.image
                PostMedia.create_post_media(type=PostMedia.MEDIA_TYPE_IMAGE,
                                            content_object=post_image,
                                            post_id=post.pk, order=0)
                post_image.save()
            logger.info('Migrated post with id:' + str(post.pk))
            migrated_posts = migrated_posts + 1

        logger.info('Migrated %d posts' % migrated_posts)
