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


class FollowersAPITests(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_followers(self):
        """
        should be able to retrieve the authenticated user linked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        followers_ids = []

        amount_of_followers = 5

        for i in range(0, amount_of_followers):
            follower = make_user()
            follower.follow_user_with_id(user.pk)
            followers_ids.append(follower.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_followers = json.loads(response.content)

        self.assertEqual(len(response_followers), amount_of_followers)

        for response_member in response_followers:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, followers_ids)

    def test_cant_retrieve_soft_deleted_followers(self):
        """
        should not be able to retrieve soft deleted followers
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followers = 5

        for i in range(0, amount_of_followers):
            follower = make_user()
            follower.follow_user_with_id(user.pk)
            follower.soft_delete()

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_followers = json.loads(response.content)

        self.assertEqual(0, len(response_followers))

    def _get_url(self):
        return reverse('followers')


class SearchFollowersAPITests(OpenbookAPITestCase):
    """
    SearchFollowersAPI
    """

    def test_can_search_followers_by_name(self):
        """
        should be able to search for linked users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followers_to_search_for = 5

        for i in range(0, amount_of_followers_to_search_for):
            follower = make_user()
            follower.follow_user_with_id(user.pk)

            follower_name = follower.profile.name
            amount_of_characters_to_query = random.randint(1, len(follower_name))
            query = follower_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followers = json.loads(response.content)
            response_members_count = len(response_followers)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_followers[0]

            self.assertEqual(retrieved_linked_member['id'], follower.id)
            follower.unfollow_user_with_id(user.pk)

    def test_can_search_followers_by_username(self):
        """
        should be able to search for linked users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followers_to_search_for = 5

        for i in range(0, amount_of_followers_to_search_for):
            follower = make_user()
            follower.follow_user_with_id(user.pk)

            follower_username = follower.username
            amount_of_characters_to_query = random.randint(1, len(follower_username))
            query = follower_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followers = json.loads(response.content)
            response_members_count = len(response_followers)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_followers[0]

            self.assertEqual(retrieved_linked_member['id'], follower.id)
            follower.unfollow_user_with_id(user.pk)

    def test_cant_search_soft_deleted_followers(self):
        """
        should not be able to search for soft deleted followers and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followers_to_search_for = 5

        for i in range(0, amount_of_followers_to_search_for):
            follower = make_user()
            follower.follow_user_with_id(user.pk)
            follower.soft_delete()

            follower_username = follower.username
            amount_of_characters_to_query = random.randint(1, len(follower_username))
            query = follower_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followers = json.loads(response.content)
            response_members_count = len(response_followers)

            self.assertEqual(0, response_members_count)


    def _get_url(self):
        return reverse('search-followers')
