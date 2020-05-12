# Create your tests here.
from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User
from faker import Faker

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user
from openbook_lists.models import List
from openbook_follows.models import Follow
from openbook_notifications.models import FollowNotification, Notification

logger = logging.getLogger(__name__)

fake = Faker()


class ReceivedFollowRequestsAPITests(OpenbookAPITestCase):
    def test_can_retrieve_received_own_follow_requests(self):
        """
        should be able to retrieve own follow requests and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        number_of_own_follow_requests = 3
        follow_requests_ids = []

        for i in range(0, number_of_own_follow_requests):
            requesting_user = make_user()
            follow_request = requesting_user.create_follow_request_for_user(user=user)
            follow_requests_ids.append(follow_request.pk)

        url = self._get_url()

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_follow_requests = json.loads(response.content)

        self.assertEqual(len(response_follow_requests), number_of_own_follow_requests)

        for response_follow_request in response_follow_requests:
            response_follow_request_id = response_follow_request.get('id')
            self.assertIn(response_follow_request_id, follow_requests_ids)

    def test_can_retrieve_max_10_received_own_follow_requests(self):
        """
        should be able to retrieve a maximum of 10 own follow requests at a time and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        max_number_of_own_follow_requests = 10

        for i in range(0, max_number_of_own_follow_requests + 1):
            requesting_user = make_user()
            requesting_user.create_follow_request_for_user(user=user)

        url = self._get_url()

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_follow_requests = json.loads(response.content)

        self.assertEqual(len(response_follow_requests), max_number_of_own_follow_requests)

    def test_cannot_retrieve_received_foreign_follow_requests(self):
        """
        should not be able to retrieve foreign follow requests and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        foreign_user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        headers = make_authentication_headers_for_user(user)

        requesting_user = make_user()
        requesting_user.create_follow_request_for_user(user=foreign_user)

        url = self._get_url()

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_follow_requests = json.loads(response.content)

        self.assertEqual(len(response_follow_requests), 0)

    def _get_url(self):
        return reverse('received-follow-requests')


class FollowAPITests(OpenbookAPITestCase):
    def test_follow(self):
        """
        should be able to follow another user on an specific list and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.is_following_user_in_list(user_to_follow, list_to_follow))

    def test_follow_in_multiple_lists(self):
        """
        should be able to follow another user on multiple lists and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        amount_of_lists = 4
        lists_to_follow_ids = []

        for i in range(amount_of_lists):
            list_to_follow = mixer.blend(List, creator=user)
            lists_to_follow_ids.append(list_to_follow.pk)

        user_to_follow = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_lists_ids = ','.join(map(str, lists_to_follow_ids))

        data = {
            'username': user_to_follow.username,
            'lists_ids': stringified_lists_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for list_id in lists_to_follow_ids:
            self.assertTrue(user.is_following_user_with_id_in_list_with_id(user_to_follow, list_id))

    def test_cannot_follow_with_existing_follow(self):
        """
        should not be able to follow a user already followed with and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = make_user()

        user.follow_user(user_to_follow, lists_ids=[list_to_follow.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_follow_oneself(self):
        """
        should not be able to follow oneself and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Follow.objects.filter(user=user, followed_user=user).count() == 0)

    def test_follow_should_create_notification(self):
        """
        should create a notification when a user is followed
        """
        user = make_user()

        auth_token = user.auth_token.key

        user_to_follow = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
        }

        url = self._get_url()

        self.client.post(url, data, **headers, format='multipart')

        self.assertTrue(FollowNotification.objects.filter(follower=user, notification__owner=user_to_follow).exists())

    def _get_url(self):
        return reverse('follow-user')


class UnfollowAPITest(OpenbookAPITestCase):
    def test_unfollow(self):
        """
        should be able to unfollow a user and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_unfollow = make_user()

        user.follow_user(user_to_unfollow, lists_ids=[list_to_follow.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_unfollow.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.is_following_user_in_list(user_to_unfollow, list_to_follow))

    def test_cannot_unfollow_from_unexisting_follow(self):
        """
        should not be able to unfollow from an unexisting follow and return 400
        """
        user = make_user()

        not_followed_user = make_user()

        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_followed_user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.is_following_user(not_followed_user))

    def test_unfollow_should_delete_follow_notification(self):
        """
        should delete the follow notification when a user is unfollowed
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_unfollow = make_user()

        user.follow_user(user_to_unfollow, lists_ids=[list_to_follow.pk])

        follow_notification = FollowNotification.objects.get(follower=user, notification__owner=user_to_unfollow)
        notification = Notification.objects.get(notification_type=Notification.FOLLOW, object_id=follow_notification.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_unfollow.username
        }

        url = self._get_url()

        self.client.post(url, data, **headers, format='multipart')

        self.assertFalse(FollowNotification.objects.filter(pk=follow_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def _get_url(self):
        return reverse('unfollow-user')


class UpdateFollowAPITest(OpenbookAPITestCase):
    def test_update_follow(self):
        """
        should be able to update an own follow and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = make_user()

        user.follow_user(user_to_follow, lists_ids=[list_to_follow.pk])

        new_list = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': new_list.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.is_following_user_in_list(user_to_follow, new_list))

    def test_update_follow_multiple_lists(self):
        """
        should be able to update an own follow of multiple lists and return 200
        """
        user = make_user()
        user_to_follow = make_user()

        initial_list_to_follow_in = mixer.blend(List, creator=user)

        user.follow_user(user_to_follow, lists_ids=[initial_list_to_follow_in.pk])

        auth_token = user.auth_token.key

        amount_of_lists = 4
        new_lists_to_follow_ids = []

        for i in range(amount_of_lists):
            list_to_follow = mixer.blend(List, creator=user)
            new_lists_to_follow_ids.append(list_to_follow.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_lists_ids = ','.join(map(str, new_lists_to_follow_ids))

        data = {
            'username': user_to_follow.username,
            'lists_ids': stringified_lists_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow = user.get_follow_for_user_with_id(user_to_follow.pk)
        follow_lists_ids = [list.pk for list in follow.lists.all()]

        self.assertEqual(len(new_lists_to_follow_ids), len(follow_lists_ids))

        for list_id in new_lists_to_follow_ids:
            self.assertIn(list_id, follow_lists_ids)

    def test_cannot_update_unexisting_follow(self):
        """
        should not be able to update an unexisting follow and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        not_followed_user = make_user()

        new_list = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_followed_user.username,
            'lists_ids': new_list.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('update-follow')
