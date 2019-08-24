from django.urls import reverse
from faker import Faker

from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_user, make_proxy_whitelisted_domain

fake = Faker()

logger = logging.getLogger(__name__)


class ProxyAuthAPITests(APITestCase):
    """
    ProxyAuthAPI tests
    """

    def test_header_required_for_proxy_auth(self):
        """
        should return 403 if the X-Proxy-Url header is not present
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_proxy_auth_does_not_allow_non_whitelisted_domain(self):
        """
        should return 403 if the X-Proxy-Url url is not in whitelisted
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        headers['HTTP_X_PROXY_URL'] = 'https://notwhitelisted.com'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_proxy_auth_allows_whitelisted_domain(self):
        """
        should return 202 if the X-Proxy-Url url is whitelisted
        """
        cache.delete(settings.POST_LINK_WHITELIST_DOMAIN_CACHE_KEY)  # clear cache value
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        headers['HTTP_X_PROXY_URL'] = 'https://www.techcrunch.com'
        make_proxy_whitelisted_domain(domain='www.techcrunch.com')
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def _get_url(self):
        return reverse('proxy-auth')
