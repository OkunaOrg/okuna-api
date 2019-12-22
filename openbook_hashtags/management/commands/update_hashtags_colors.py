from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.helpers import get_random_pastel_color
from openbook_common.utils.model_loaders import get_hashtag_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update the hashtags colors'

    def handle(self, *args, **options):
        Hashtag = get_hashtag_model()

        processed_hashtags = 0

        for hashtag in Hashtag.objects.all().iterator():
            with transaction.atomic():
                new_color = get_random_pastel_color()
                hashtag.color = new_color
                hashtag.save()

            logger.info('Processed hashtags for post with name:' + str(hashtag.name))
            processed_hashtags = processed_hashtags + 1

        logger.info('Updated %d hashtags colors' % processed_hashtags)
