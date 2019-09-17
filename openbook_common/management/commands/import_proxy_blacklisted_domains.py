import ipaddress
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from tldextract import tldextract

from openbook_common.models import ProxyBlacklistedDomain
from openbook_common.utils.model_loaders import get_user_invite_model, get_badge_model

import logging
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

url_validator = URLValidator()


class Command(BaseCommand):
    help = 'Imports a list of proxy blacklisted domains'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='The file to import the blacklisted domains from')

    def handle(self, *args, **options):

        imported_domains = 0
        already_existing_domains = 0

        file_path = options.get('file', None)

        with open(file_path, newline='') as file:
            line = file.readline()

            while line:
                url = line
                line = file.readline()

                if not urlparse(url).scheme:
                    url = 'http://' + line

                # This uses a list of public suffixes
                tld_extract_result = tldextract.extract(url)

                if tld_extract_result.subdomain:
                    url_full_domain = '.'.join(
                        [tld_extract_result.subdomain, tld_extract_result.domain, tld_extract_result.suffix])
                elif tld_extract_result.suffix:
                    url_full_domain = '.'.join(
                        [tld_extract_result.domain, tld_extract_result.suffix])
                else:
                    url_full_domain = tld_extract_result.domain

                if ProxyBlacklistedDomain.objects.filter(domain=url_full_domain).exists():
                    logger.info('Domain %s already exists, not importing.' % url_full_domain)
                    already_existing_domains += 1
                    continue

                ProxyBlacklistedDomain.objects.create(domain=url_full_domain)
                logger.info('Imported domain %s successfully.' % url_full_domain)
                imported_domains += 1

            logger.info('Finished. Imported %d domains and skipped %d as they already existed' % (
                imported_domains, already_existing_domains))
