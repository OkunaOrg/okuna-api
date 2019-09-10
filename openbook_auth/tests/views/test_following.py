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


class FollowingsAPITests(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_followings(self):
        """
        should be able to retrieve the authenticated user linked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        followings_ids = []

        amount_of_followings = 5

        for i in range(0, amount_of_followings):
            following_user = make_user()
            user.follow_user_with_id(following_user.pk)
            followings_ids.append(following_user.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_followings = json.loads(response.content)

        self.assertEqual(len(response_followings), amount_of_followings)

        for response_member in response_followings:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, followings_ids)

    def test_cant_retrieve_soft_deleted_followings(self):
        """
        should be able to retrieve the authenticated user linked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        followings_ids = []

        amount_of_followings = 5

        for i in range(0, amount_of_followings):
            following_user = make_user()
            user.follow_user_with_id(following_user.pk)
            followings_ids.append(following_user.pk)
            following_user.soft_delete()

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_followings = json.loads(response.content)

        self.assertEqual(0, len(response_followings))

    def _get_url(self):
        return reverse('followings')


class SearchFollowingsAPITests(OpenbookAPITestCase):
    """
    SearchFollowingsAPI
    """

    def test_can_search_followings_by_name(self):
        """
        should be able to search for linked users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followings_to_search_for = 5

        for i in range(0, amount_of_followings_to_search_for):
            following_user = make_user()
            user.follow_user_with_id(following_user.pk)

            following_name = following_user.profile.name
            amount_of_characters_to_query = random.randint(1, len(following_name))
            query = following_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followings = json.loads(response.content)
            response_members_count = len(response_followings)

            self.assertEqual(response_members_count, 1)
            retrieved_user = response_followings[0]

            self.assertEqual(retrieved_user['id'], following_user.id)
            user.unfollow_user_with_id(following_user.pk)

    def test_can_search_followings_by_username(self):
        """
        should be able to search for linked users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followings_to_search_for = 5

        for i in range(0, amount_of_followings_to_search_for):
            following_user = make_user()
            user.follow_user_with_id(following_user.pk)

            following_name = following_user.username
            amount_of_characters_to_query = random.randint(1, len(following_name))
            query = following_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followings = json.loads(response.content)
            response_members_count = len(response_followings)

            self.assertEqual(response_members_count, 1)
            retrieved_user = response_followings[0]

            self.assertEqual(retrieved_user['id'], following_user.id)
            user.unfollow_user_with_id(following_user.pk)

    def test_cant_search_soft_deleted_followings(self):
        """
        should not be able to search for soft deleted followings by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_followings_to_search_for = 5

        for i in range(0, amount_of_followings_to_search_for):
            following_user = make_user()
            user.follow_user_with_id(following_user.pk)
            following_user.soft_delete()

            following_name = following_user.username
            amount_of_characters_to_query = random.randint(1, len(following_name))
            query = following_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_followings = json.loads(response.content)
            response_members_count = len(response_followings)

            self.assertEqual(0, response_members_count)

    def _get_url(self):
        return reverse('search-followings')
