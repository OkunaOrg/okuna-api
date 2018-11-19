from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import logging
import json

from openbook_common.tests.helpers import make_emoji_group, make_emoji, make_user, make_authentication_headers_for_user

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


class TestEmojiGroups(APITestCase):
    """
    EmojiGroups API
    """

    url = reverse('emoji-groups')

    def test_can_retrieve_emoji_groups(self):
        """
         should be able to retrieve the emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group()
            group_ids.append(group.pk)

        response = self.client.get(self.url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)

        self.assertEqual(len(response_groups), len(group_ids))

        for response_group in response_groups:
            response_list_id = response_group.get('id')
            self.assertIn(response_list_id, group_ids)
