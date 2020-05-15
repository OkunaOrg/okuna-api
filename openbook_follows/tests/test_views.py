# Create your tests here.
from unittest import mock

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
from openbook_follows.models import Follow, FollowRequest
from openbook_notifications.models import FollowNotification, Notification, FollowRequestNotification, \
    FollowRequestApprovedNotification

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


class RequestToFollowUserAPITests(OpenbookAPITestCase):
    def test_can_request_to_follow_private_user(self):
        """
        should be able to request to follow a private user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        data = {
            'username': user_to_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_request_to_follow.has_follow_request_from_user(user=user))

    def test_cannot_request_to_follow_oneself(self):
        """
        should not be able to request to follow oneself user and return 500
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_follow_request_from_user(user=user))

    def test_cannot_request_to_follow_private_user_more_than_once(self):
        """
        should not be able to request to follow a private user more than once and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        user.create_follow_request_for_user(user=user_to_request_to_follow)

        data = {
            'username': user_to_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(FollowRequest.objects.filter(creator=user, target_user=user_to_request_to_follow).count(), 1)

    def test_cannot_request_to_follow_user_if_not_private(self):
        """
        should not be able to request to follow a non-private user and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        for visibility_keyword, visibility_name in User.VISIBILITY_TYPES:
            if visibility_keyword == User.VISIBILITY_TYPE_PRIVATE:
                return

            user_to_request_to_follow = make_user(visibility=visibility_keyword)

            data = {
                'username': user_to_request_to_follow.username,
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            self.assertFalse(user_to_request_to_follow.has_follow_request_from_user(user=user))

    def test_requesting_to_follow_user_creates_database_notification(self):
        """
        should create a database notification when sending a request notification to a user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        data = {
            'username': user_to_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(FollowRequestNotification.objects.filter(notification__owner=user_to_request_to_follow,
                                                                  follow_request__creator=user).count(), 1)

    @mock.patch('openbook_notifications.helpers.send_follow_request_push_notification')
    def test_requesting_to_follow_user_creates_push_notification(self, send_follow_request_push_notification):
        """
        should create a push notification when sending a request notification to a user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        data = {
            'username': user_to_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        follow_request = FollowRequest.objects.get(creator=user, target_user=user_to_request_to_follow)

        send_follow_request_push_notification.assert_called_with(
            follow_request=follow_request)

    @mock.patch('openbook_notifications.helpers._send_notification_to_user')
    def test_requesting_to_follow_user_does_not_create_push_notification_if_disabled(self, _send_notification_to_user):
        """
        should not create push notification when sending a request notification to a user if disabled
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        user_to_request_to_follow.update_notifications_settings(follow_request_notifications=False)

        data = {
            'username': user_to_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        _send_notification_to_user.assert_not_called()

    def _get_url(self):
        return reverse('request-to-follow-user')


class CancelRequestToFollowUserAPITests(OpenbookAPITestCase):
    def test_can_cancel_request_to_follow_private_user(self):
        """
        should be able to cancel a request to follow a private user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_cancel_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        user.create_follow_request_for_user(user_to_cancel_request_to_follow)

        data = {
            'username': user_to_cancel_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user_to_cancel_request_to_follow.has_follow_request_from_user(user=user))

    def test_cannot_cancel_request_to_follow_user_if_not_exists(self):
        """
        should not be able to cancel a non existing request to follow and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_cancel_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        data = {
            'username': user_to_cancel_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelling_a_request_to_follow_deletes_database_notification(self):
        """
        should delete the database notification when cancelling a request notification to a user
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_cancel_request_to_follow = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        user.create_follow_request_for_user(user_to_cancel_request_to_follow)

        data = {
            'username': user_to_cancel_request_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user_to_cancel_request_to_follow.has_follow_request_from_user(user=user))

        self.assertFalse(FollowRequestNotification.objects.filter(notification__owner=user_to_cancel_request_to_follow,
                                                                  follow_request__creator=user).exists())

    def _get_url(self):
        return reverse('cancel-request-to-follow-user')


class ApproveUserFollowRequestAPITests(OpenbookAPITestCase):
    def test_approving_a_follow_request_follows_the_approving_user(self):
        """
        should be able to approve a follow request and automatically follow the approving user and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user_requesting_to_follow.is_following_user(user=user))

    def test_approving_a_follow_request_deletes_the_follow_request(self):
        """
        when approving a follow request it should delete the follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_follow_request_from_user(user=user_requesting_to_follow))

    def test_approving_a_follow_request_deletes_the_follow_request_database_notification(self):
        """
        when approving a follow request it should delete the follow request database notification
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(FollowRequestNotification.objects.filter(
            notification__owner=user,
            follow_request__creator=user_requesting_to_follow).exists())

    def test_approving_a_follow_request_creates_database_notification(self):
        """
        should create a database notification when approving a follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(FollowRequestApprovedNotification.objects.filter(notification__owner=user_requesting_to_follow,
                                                                          follow__followed_user=user).count(), 1)

    @mock.patch('openbook_notifications.helpers.send_follow_request_approved_push_notification')
    def test_approving_a_follow_request_send_approved_push_notification(self, send_follow_request_approved_push_notification):
        """
        should send a follow request approved push notification when approving a follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow = Follow.objects.get(followed_user=user, user=user_requesting_to_follow)

        send_follow_request_approved_push_notification.assert_called_with(
            follow=follow)

    @mock.patch('openbook_notifications.helpers.send_follow_push_notification')
    def test_approving_a_follow_request_does_not_send_a_follow_push_notification(self, send_follow_push_notification):
        """
        should not send a user followed push notification when approving a follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        send_follow_push_notification.assert_not_called()

    @mock.patch('openbook_notifications.helpers._send_notification_to_user')
    def test_approving_a_follow_request_does_not_create_push_notification_if_disabled(self, _send_notification_to_user):
        """
        should not create push notification when approving a request notification to a user if disabled
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.update_notifications_settings(follow_request_approved_notifications=False)
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        _send_notification_to_user.reset_mock()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(_send_notification_to_user.call_count, 0)

    def test_cant_approve_non_existing_follow_request(self):
        """
        should not be able to approve a nonexisting request and return 400
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_requesting_to_follow.is_following_user(user=user))

    def _get_url(self):
        return reverse('approve-user-follow-request')


class RejectUserFollowRequestAPITests(OpenbookAPITestCase):
    def test_rejecting_a_follow_request_does_not_follow_the_rejecting_user(self):
        """
        should be able to reject a follow request and automatically follow the rejecting user and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user_requesting_to_follow.is_following_user(user=user))

    def test_rejecting_a_follow_request_deletes_the_follow_request(self):
        """
        when rejecting a follow request it should delete the follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_follow_request_from_user(user=user_requesting_to_follow))

    def test_rejecting_a_follow_request_deletes_the_follow_request_database_notification(self):
        """
        when rejecting a follow request it should delete the follow request database notification
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(FollowRequestNotification.objects.filter(
            notification__owner=user,
            follow_request__creator=user_requesting_to_follow).exists())

    def test_rejecting_a_follow_request_does_not_create_database_notification(self):
        """
        should not create a database notification when rejecting a follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(FollowRequestApprovedNotification.objects.filter(notification__owner=user_requesting_to_follow,
                                                                          follow__followed_user=user).exists())

    @mock.patch('openbook_notifications.helpers.send_follow_request_approved_push_notification')
    def test_rejecting_a_follow_request_does_not_create_push_notification(self,
                                                                          send_follow_request_approved_push_notification):
        """
        should create a push notification when rejecting a follow request
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        send_follow_request_approved_push_notification.assert_not_called()

    def test_cant_reject_non_existing_follow_request(self):
        """
        should not be able to reject a nonexisting request and return 400
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()

        data = {
            'username': user_requesting_to_follow.username,
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_requesting_to_follow.is_following_user(user=user))

    def _get_url(self):
        return reverse('reject-user-follow-request')


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
