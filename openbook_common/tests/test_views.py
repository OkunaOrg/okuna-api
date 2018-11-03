from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import logging
import json

logger = logging.getLogger(__name__)


class TimeAPITests(APITestCase):
    """
    TimeAPITests
    """

    def test_timezone_set(self):
        """
        should set the timezone provided in the Time-Zone header
        """
        url = self._get_url()
        timezone_to_set = 'America/Mexico_City'
        header = {'HTTP_TIME_ZONE': timezone_to_set}
        response = self.client.get(url, **header)
        parsed_response = json.loads(response.content)
        self.assertEqual(parsed_response['timezone'], timezone_to_set)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _get_url(self):
        return reverse('time')


class TestHealth(APITestCase):
    """
    Health API
    """

    url = reverse('health')

    def test_should_say_hello(self):
        response = self.client.get(self.url)
        self.assertTrue(response.status_code, status.HTTP_200_OK)
