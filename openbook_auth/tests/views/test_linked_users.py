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


class LinkedUsersAPITests(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_linked_users(self):
        """
        should be able to retrieve the authenticated user linked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        linked_users_ids = []
        amount_of_followers_linked_users = 5
        amount_of_connected_linked_users = 5

        amount_of_linked_users = amount_of_connected_linked_users + amount_of_followers_linked_users

        for i in range(0, amount_of_followers_linked_users):
            linked_follower_user = make_user()
            linked_follower_user.follow_user_with_id(user.pk)
            linked_users_ids.append(linked_follower_user.pk)

        for i in range(0, amount_of_connected_linked_users):
            linked_connected_user = make_user()
            linked_connected_user.connect_with_user_with_id(user.pk)
            user.confirm_connection_with_user_with_id(linked_connected_user.pk)
            linked_users_ids.append(linked_connected_user.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_linked_users = json.loads(response.content)

        self.assertEqual(len(response_linked_users), amount_of_linked_users)

        for response_member in response_linked_users:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, linked_users_ids)

    def _get_url(self):
        return reverse('linked-users')


class SearchLinkedUsersAPITests(OpenbookAPITestCase):
    """
    SearchLinkedUsersAPI
    """

    def test_can_search_linked_users_by_name(self):
        """
        should be able to search for linked users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_linked_users_to_search_for = 5

        for i in range(0, amount_of_linked_users_to_search_for):
            linked_user = make_user()
            linked_user.follow_user_with_id(user.pk)

            linked_user_name = linked_user.profile.name
            amount_of_characters_to_query = random.randint(1, len(linked_user_name))
            query = linked_user_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_linked_users = json.loads(response.content)
            response_members_count = len(response_linked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_linked_users[0]

            self.assertEqual(retrieved_linked_member['id'], linked_user.id)
            linked_user.unfollow_user_with_id(user.pk)

    def test_can_search_linked_users_by_username(self):
        """
        should be able to search for linked users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_linked_users_to_search_for = 5

        for i in range(0, amount_of_linked_users_to_search_for):
            linked_user = make_user()
            linked_user.follow_user_with_id(user.pk)

            linked_user_username = linked_user.username
            amount_of_characters_to_query = random.randint(1, len(linked_user_username))
            query = linked_user_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_linked_users = json.loads(response.content)
            response_members_count = len(response_linked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_linked_users[0]

            self.assertEqual(retrieved_linked_member['id'], linked_user.id)
            linked_user.unfollow_user_with_id(user.pk)

    def _get_url(self):
        return reverse('search-linked-users')


