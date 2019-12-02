import random
from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user

fake = Faker()

logger = logging.getLogger(__name__)


class BlockedUsersAPITests(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_blocked_users(self):
        """
        should be able to retrieve the authenticated user blocked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        blocked_users_ids = []
        amount_of_blocked_users = 5

        for i in range(0, amount_of_blocked_users):
            blocked_user = make_user()
            user.block_user_with_id(blocked_user.pk)
            blocked_users_ids.append(blocked_user.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_blocked_users = json.loads(response.content)

        self.assertEqual(len(response_blocked_users), amount_of_blocked_users)

        for response_member in response_blocked_users:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, blocked_users_ids)

    def _get_url(self):
        return reverse('blocked-users')


class SearchBlockedUsersAPITests(OpenbookAPITestCase):
    """
    SearchBlockedUsersAPI
    """

    def test_can_search_blocked_users_by_name(self):
        """
        should be able to search for blocked users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_blocked_users_to_search_for = 5

        for i in range(0, amount_of_blocked_users_to_search_for):
            blocked_user = make_user()
            user.block_user_with_id(blocked_user.pk)

            blocked_user_name = blocked_user.profile.name
            amount_of_characters_to_query = random.randint(1, len(blocked_user_name))
            query = blocked_user_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_blocked_users = json.loads(response.content)
            response_members_count = len(response_blocked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_blocked_member = response_blocked_users[0]

            self.assertEqual(retrieved_blocked_member['id'], blocked_user.id)
            user.unblock_user_with_id(blocked_user.pk)

    def test_can_search_blocked_users_by_username(self):
        """
        should be able to search for blocked users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_blocked_users_to_search_for = 5

        for i in range(0, amount_of_blocked_users_to_search_for):
            blocked_user = make_user()
            user.block_user_with_id(blocked_user.pk)

            blocked_user_username = blocked_user.username
            amount_of_characters_to_query = random.randint(1, len(blocked_user_username))
            query = blocked_user_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_blocked_users = json.loads(response.content)
            response_members_count = len(response_blocked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_blocked_member = response_blocked_users[0]

            self.assertEqual(retrieved_blocked_member['id'], blocked_user.id)
            user.unblock_user_with_id(blocked_user.pk)

    def _get_url(self):
        return reverse('search-blocked-users')


