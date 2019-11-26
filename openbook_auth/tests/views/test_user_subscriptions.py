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


class UserSubscriptionsAPITests(OpenbookAPITestCase):
    """
    UserSubscriptionsAPI Tests
    """
    def test_can_retrieve_user_subscriptions(self):
        """
        should be able to retrieve the authenticated users subscriptions
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_subscriptions_ids = []

        amount_of_user_subscriptions = 5

        for i in range(0, amount_of_user_subscriptions):
            user_to_subscribe = make_user()
            user.subscribe_to_notifications_for_user_with_username(user_to_subscribe.username)
            user_subscriptions_ids.append(user_to_subscribe.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_user_subscriptions = json.loads(response.content)

        self.assertEqual(len(response_user_subscriptions), amount_of_user_subscriptions)

        for response_member in response_user_subscriptions:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, user_subscriptions_ids)

    def test_cant_retrieve_soft_deleted_user_subscriptions(self):
        """
        should not be able to retrieve the authenticated user subscriptions users that are soft deleted
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_subscriptions_ids = []

        amount_of_user_subscriptions = 5

        for i in range(0, amount_of_user_subscriptions):
            user_to_subscribe = make_user()
            user.subscribe_to_notifications_for_user_with_username(user_to_subscribe.username)
            user_subscriptions_ids.append(user_to_subscribe.pk)
            user_to_subscribe.soft_delete()

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_user_subscriptions = json.loads(response.content)

        self.assertEqual(0, len(response_user_subscriptions))

    def _get_url(self):
        return reverse('user-subscriptions')


class SearchUserSubscriptionsAPITests(OpenbookAPITestCase):
    """
    SearchUserSubscriptionsAPI
    """

    def test_can_search_user_subscriptions_by_name(self):
        """
        should be able to search for subscriptions users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_user_subscriptions_to_search_for = 5

        for i in range(0, amount_of_user_subscriptions_to_search_for):
            user_to_subscribe = make_user()
            user.subscribe_to_notifications_for_user_with_username(user_to_subscribe.username)

            subscription_name = user_to_subscribe.profile.name
            amount_of_characters_to_query = random.randint(1, len(subscription_name))
            query = subscription_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_user_subscriptions = json.loads(response.content)
            response_members_count = len(response_user_subscriptions)

            self.assertEqual(response_members_count, 1)
            retrieved_user = response_user_subscriptions[0]

            self.assertEqual(retrieved_user['id'], user_to_subscribe.id)
            user.unsubscribe_from_notifications_for_user_with_username(user_to_subscribe.username)

    def test_can_search_user_subscriptions_by_username(self):
        """
        should be able to search for subscriptions users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_user_subscriptions_to_search_for = 5

        for i in range(0, amount_of_user_subscriptions_to_search_for):
            user_to_subscribe = make_user()
            user.subscribe_to_notifications_for_user_with_username(user_to_subscribe.username)

            subscription_name = user_to_subscribe.username
            amount_of_characters_to_query = random.randint(1, len(subscription_name))
            query = subscription_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_user_subscriptions = json.loads(response.content)
            response_members_count = len(response_user_subscriptions)

            self.assertEqual(response_members_count, 1)
            retrieved_user = response_user_subscriptions[0]

            self.assertEqual(retrieved_user['id'], user_to_subscribe.id)
            user.unsubscribe_from_notifications_for_user_with_username(user_to_subscribe.username)

    def test_cant_search_soft_deleted_user_subscriptions(self):
        """
        should not be able to search for soft deleted user subscriptions by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_user_subscriptions_to_search_for = 5

        for i in range(0, amount_of_user_subscriptions_to_search_for):
            user_to_subscribe = make_user()
            user.subscribe_to_notifications_for_user_with_username(user_to_subscribe.username)
            user_to_subscribe.soft_delete()

            subscription_name = user_to_subscribe.username
            amount_of_characters_to_query = random.randint(1, len(subscription_name))
            query = subscription_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_user_subscriptions = json.loads(response.content)
            response_members_count = len(response_user_subscriptions)

            self.assertEqual(0, response_members_count)

    def _get_url(self):
        return reverse('search-user-subscriptions')
