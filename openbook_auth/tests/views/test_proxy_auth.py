from django.urls import reverse
from faker import Faker

from rest_framework import status
from rest_framework.test import APITestCase
import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_user, make_proxy_blacklisted_domain

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

    def test_proxy_auth_allows_non_blacklisted_domain(self):
        """
        should return 403 if the X-Proxy-Url url is not in whitelisted
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        headers['HTTP_X_PROXY_URL'] = 'https://notblacklisted.com'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_proxy_auth_disallows_blacklisted_domain(self):
        """
        should return 403 if the X-Proxy-Url url is blacklisted
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        headers['HTTP_X_PROXY_URL'] = 'https://www.techcrunch.com'
        make_proxy_blacklisted_domain(domain='techcrunch.com')
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_proxy_auth_disallows_invalid_domain(self):
        """
        should return 403 if the X-Proxy-Url url is invalid
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        headers['HTTP_X_PROXY_URL'] = 'https://wwwinvalic.poptaer'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_proxy_auth_disallows_blacklisted_root_domain(self):
        """
        should disallow when calling with a blacklisted root domain and return 403
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        make_proxy_blacklisted_domain(domain='blogspot.com')

        headers['HTTP_X_PROXY_URL'] = 'test.blogspot.com'
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_proxy_auth_disallows_blacklisted_subdomain_domain(self):
        """
        should disallow when calling with a blacklisted subdomain domain and return 403
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        make_proxy_blacklisted_domain(domain='test.blogspot.com')

        headers['HTTP_X_PROXY_URL'] = 'test.blogspot.com'
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_allows_non_blacklisted_root_domain_with_blacklisted_subdomain(self):
        """
        should allow when calling with a non blacklisted root domain that also has a blacklisted subdomain and return 403
        """
        url = self._get_url()
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        make_proxy_blacklisted_domain(domain='test.blogspot.com')

        headers['HTTP_X_PROXY_URL'] = 'blogspot.com'
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def _get_url(self):
        return reverse('proxy-auth')
