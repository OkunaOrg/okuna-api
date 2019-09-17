from django.core.management.base import BaseCommand

from openbook_common.models import ProxyBlacklistedDomain
from openbook_common.utils.model_loaders import get_user_invite_model, get_badge_model

import logging
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

url_validator = URLValidator()


class Command(BaseCommand):
    help = 'Flush all of the proxy blacklisted domains'

    def handle(self, *args, **options):
        ProxyBlacklistedDomain.objects.all().delete()
