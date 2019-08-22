from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import json

from openbook_common.tests.helpers import make_emoji_group, make_emoji, make_user, make_authentication_headers_for_user

logger = logging.getLogger(__name__)


class TimeAPITests(OpenbookAPITestCase):
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


class TestHealth(OpenbookAPITestCase):
    """
    Health API
    """

    url = reverse('health')

    def test_should_say_hello(self):
        response = self.client.get(self.url)
        self.assertTrue(response.status_code, status.HTTP_200_OK)


class TestEmojiGroups(OpenbookAPITestCase):
    """
    EmojiGroups API
    """

    def test_can_retrieve_non_reaction_emoji_groups(self):
        """
         should be able to retrieve non post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=False)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)
        response_groups_ids = [group['id'] for group in response_groups]

        self.assertEqual(len(response_groups), len(group_ids))

        for group_id in group_ids:
            self.assertIn(group_id, response_groups_ids)

    def test_cannot_retrieve_reactions_emoji_groups(self):
        """
         should not able to retrieve post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=True)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)

        self.assertEqual(len(response_groups), 0)

    def _get_url(self):
        return reverse('emoji-groups')
