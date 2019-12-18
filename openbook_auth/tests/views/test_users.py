from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import json
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_fake_post_text
from openbook_common.utils.model_loaders import get_user_notifications_subscription_model

fake = Faker()

logger = logging.getLogger(__name__)


class SearchUsersAPITests(OpenbookAPITestCase):
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

    def test_cant_query_blocked_user(self):
        user = make_user()

        user_to_query = make_user()
        user.block_user_with_id(user_id=user_to_query.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        response = self.client.get(url, {
            'query': user_to_query.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_cant_query_blocking_user(self):
        user = make_user()

        user_to_query = make_user()
        user_to_query.block_user_with_id(user_id=user.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        response = self.client.get(url, {
            'query': user_to_query.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

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

    def test_cannot_query_soft_deleted_user(self):
        user = make_user()
        user_to_search_for = make_user()
        user_to_search_for.soft_delete()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        response = self.client.get(url, {
            'query': user_to_search_for,
        }, **headers)

        parsed_reponse = json.loads(response.content)

        self.assertEqual(0, len(parsed_reponse))

    def _get_url(self):
        return reverse('search-users')


class GetUserAPITests(OpenbookAPITestCase):
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

    def test_cant_retrieve_blocked_user(self):
        """
        should not be able to retrieve a blocked user and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_retrieve = make_user()
        user.block_user_with_id(user_id=user_to_retrieve.pk)

        url = self._get_url(user_to_retrieve)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_retrieve_blocking_user(self):
        """
        should not be able to retrieve a blocking user and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_retrieve = make_user()
        user_to_retrieve.block_user_with_id(user_id=user.pk)

        url = self._get_url(user_to_retrieve)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_retrieve_soft_deleted_user(self):
        """
        should not be able to retrieve a soft deleted user and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_retrieve = make_user()
        user_to_retrieve.soft_delete()

        url = self._get_url(user_to_retrieve)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def _get_url(self, user):
        return reverse('get-user', kwargs={
            'user_username': user.username
        })


class BlockUserAPITests(OpenbookAPITestCase):
    """
    BlockUserAPI
    """
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_block_user(self):
        """
        should be able to block a user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        url = self._get_url(user_to_block)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.has_blocked_user_with_id(user_id=user_to_block.pk))

    def test_cannot_block_already_blocked_user(self):
        """
        should not be able to block an already blocked user and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()
        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(user_to_block)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(user.has_blocked_user_with_id(user_id=user_to_block.pk))

    def test_cannot_block_blocking_user(self):
        """
        should not be able to block a blocking user and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        blocking_user = make_user()
        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(blocking_user)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(blocking_user.has_blocked_user_with_id(user_id=user.pk))

    def test_disconnects_from_user(self):
        """
        should disconnect from the blocked user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.connect_with_user_with_id(user_id=user_to_block.pk)
        user_to_block.confirm_connection_with_user_with_id(user_id=user.pk)

        url = self._get_url(user_to_block)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.is_connected_with_user_with_id(user_id=user_to_block.pk))

    def test_unfollows_user(self):
        """
        should unfollow the blocked user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(user_to_block)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.is_following_user_with_id(user_id=user_to_block.pk))

    def test_gets_unfollowed_by_blocked_user(self):
        """
        should be unfollowed by the blocked user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user_to_block.follow_user_with_id(user_id=user.pk)

        url = self._get_url(user_to_block)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user_to_block.is_following_user_with_id(user_id=user_to_block.pk))

    def test_a_blocking_user_should_remove_notifications_subscriptions(self):
        """
        blocking a user should remove notifications subscriptions for both
        """
        user = make_user()
        user_to_block = make_user()
        headers = make_authentication_headers_for_user(user)

        user.enable_new_post_notifications_for_user_with_username(username=user_to_block.username)
        user_to_block.enable_new_post_notifications_for_user_with_username(username=user.username)

        url = self._get_url(user_to_block)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_block).exists())
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user_to_block, user=user).exists())

    def test_blocking_user_should_remove_their_notifications_subscriptions(self):
        """
        a blocking user should remove notifications subscriptions for both
        """
        user = make_user()
        blocking_user = make_user()
        headers = make_authentication_headers_for_user(blocking_user)

        blocking_user.enable_new_post_notifications_for_user_with_username(username=user.username)
        user.enable_new_post_notifications_for_user_with_username(username=blocking_user.username)

        url = self._get_url(user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=blocking_user, user=user).exists())
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user, user=blocking_user).exists())

    def _get_url(self, user):
        return reverse('block-user', kwargs={
            'user_username': user.username
        })


class UnblockUserAPITests(OpenbookAPITestCase):
    """
    UnblockUserAPI
    """

    def test_can_unblock_blocked_user(self):
        """
        should be able to unblock a blocked user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        blocked_user = make_user()
        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(blocked_user)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.has_blocked_user_with_id(user_id=blocked_user.pk))

    def test_cannot_unblock_not_blocked_user(self):
        """
        should not be able to unblock a not blocked user and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        blocked_user = make_user()

        url = self._get_url(blocked_user)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_blocked_user_with_id(user_id=blocked_user.pk))

    def test_cannot_unblock_unblocking_user(self):
        """
        should not be able to unblock a blocking user and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        blocking_user = make_user()
        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(blocking_user)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(blocking_user.has_blocked_user_with_id(user_id=user.pk))

    def _get_url(self, user):
        return reverse('unblock-user', kwargs={
            'user_username': user.username
        })


class SubscribeToUserNotificationsAPITests(OpenbookAPITestCase):
    """
    SubscribeToUserNotificationsAPI
    """

    def test_can_subscribe_to_notifications_from_user(self):
        """
        should be able to subscribe to a user and return 201
        """
        user = make_user()
        user_to_subscribe = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url(user_to_subscribe)
        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertTrue(UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_subscribe).exists())
        self.assertTrue(
            UserNotificationsSubscription.objects.get(subscriber=user, user=user_to_subscribe).new_post_notifications)

    def test_cannot_subscribe_to_own_notifications(self):
        """
        should nt be able to subscribe to a own notifications and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url(user)
        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user, user=user).exists())

    def test_cannot_subscribe_to_notifications_from_user_if_already_subscribed(self):
        """
        should not be able to subscribe to a user if already subscribed and return 400
        """
        user = make_user()
        user_to_subscribe = make_user()
        headers = make_authentication_headers_for_user(user)

        user.enable_new_post_notifications_for_user_with_username(username=user_to_subscribe.username)

        url = self._get_url(user_to_subscribe)
        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertEqual(UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_subscribe).count(),
                         1)

    def test_cannot_subscribe_to_notifications_from_user_if_user_has_been_blocked(self):
        """
        should not be able to subscribe to a user if blocked and return 403
        """
        user = make_user()
        user_to_subscribe = make_user()
        headers = make_authentication_headers_for_user(user)

        user.block_user_with_id(user_id=user_to_subscribe.id)

        url = self._get_url(user_to_subscribe)
        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_subscribe).exists())

    def test_cannot_subscribe_to_notifications_from_user_if_user_has_blocked_us(self):
        """
        should not be able to subscribe to a user if they have blocked subscriber and return 403
        """
        user = make_user()
        user_to_subscribe = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_subscribe.block_user_with_id(user_id=user.id)

        url = self._get_url(user_to_subscribe)
        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_subscribe).exists())

    def test_can_unsubscribe_to_notifications_from_user(self):
        """
        should be able to unsubscribe to a user and return 200
        """
        user = make_user()
        user_to_unsubscribe = make_user()
        headers = make_authentication_headers_for_user(user)
        # first subscribe to that user
        user.enable_new_post_notifications_for_user_with_username(username=user_to_unsubscribe.username)

        url = self._get_url(user_to_unsubscribe)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(UserNotificationsSubscription.objects.get(subscriber=user, user=user_to_unsubscribe).
                         new_post_notifications)

    def test_cannot_unsubscribe_to_notifications_from_user_if_already_unsubscribed(self):
        """
        should not be able to unsubscribe to a user if already unsubscribed and return 400
        """
        user = make_user()
        user_to_unsubscribe = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url(user_to_unsubscribe)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        UserNotificationsSubscription = get_user_notifications_subscription_model()
        self.assertFalse(
            UserNotificationsSubscription.objects.filter(subscriber=user, user=user_to_unsubscribe).exists())

    def _get_url(self, user):
        return reverse('subscribe-user-new-post-notifications', kwargs={
            'user_username': user.username
        })


class GetUserPostsCountAPITests(OpenbookAPITestCase):
    def test_can_retrieve_posts_count(self):
        """
        should be able to retrieve the posts count and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        target_user = make_user()

        amount_of_posts = 5

        for i in range(0, amount_of_posts):
            target_user.create_public_post(
                text=make_fake_post_text()
            )

        url = self._get_url(user_username=target_user.username)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('posts_count', parsed_response)
        response_posts_count = parsed_response['posts_count']

        self.assertEqual(response_posts_count, amount_of_posts)

    def _get_url(self, user_username):
        return reverse('user-posts-count', kwargs={
            'user_username': user_username
        })
