from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging
import json
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user

fake = Faker()

logger = logging.getLogger(__name__)


class SearchUsersAPITests(APITestCase):
    """
    UsersAPI
    """

    def test_can_query_users(self):
        user = make_user()
        user.username = 'lilwayne'
        user.save()

        user_b = make_user()
        user_b.username = 'lilscoop'
        user_b.save()

        user_c = make_user()
        user_c.profile.name = 'lilwhat'
        user_c.profile.save()

        lil_users = [user, user_b, user_c]

        user_d = make_user()
        user_d.username = 'lolwayne'
        user_d.save()

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        response = self.client.get(url, {
            'query': 'lil'
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), len(lil_users))

        response_usernames = [user['username'] for user in parsed_response]

        for lil_user in lil_users:
            self.assertIn(lil_user.username, response_usernames)

    def test_can_limit_amount_of_queried_users(self):
        total_users = 10
        limited_users = 5

        for i in range(total_users):
            user = make_user()
            user.profile.name = 'John Cena'
            user.profile.save()

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        response = self.client.get(url, {
            'query': 'john',
            'count': limited_users
        }, **headers)

        parsed_reponse = json.loads(response.content)

        self.assertEqual(len(parsed_reponse), limited_users)

    def _get_url(self):
        return reverse('search-users')


class GetUserAPITests(APITestCase):
    """
    UserAPI
    """

    def test_can_retrieve_user(self):
        """
        should be able to retrieve a user when authenticated and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('username', parsed_response)
        response_username = parsed_response['username']
        self.assertEqual(response_username, user.username)

    def _get_url(self, user):
        return reverse('get-user', kwargs={
            'user_username': user.username
        })
