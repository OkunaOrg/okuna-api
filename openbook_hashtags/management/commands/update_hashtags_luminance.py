import spectra
from django.core.management.base import BaseCommand
import logging

from django.db import transaction

from openbook_common.utils.helpers import get_random_pastel_color
from openbook_common.utils.model_loaders import get_hashtag_model

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update the hashtags luminance'

    def add_arguments(self, parser):
        parser.add_argument('--luminance', type=int, help='The luminance to change')

    def handle(self, *args, **options):
        luminance = options.get('luminance', None)

        if not luminance:
            raise Exception('--luminance is required')

        if luminance > 100 or luminance < -100:
            raise Exception('Luminance must be in between -100 and 100')

        Hashtag = get_hashtag_model()

        processed_hashtags = 0

        for hashtag in Hashtag.objects.all().iterator():
            with transaction.atomic():
                color = spectra.html(hashtag.color)
                if luminance > 0:
                    color = color.brighten(luminance)
                else:
                    color = color.darken(luminance * -1)
                hashtag.color = color.hexcode
                hashtag.save()

            logger.info('Processed hashtags for post with name:' + str(hashtag.name))
            processed_hashtags = processed_hashtags + 1

        logger.info('Updated %d hashtags colors' % processed_hashtags)
