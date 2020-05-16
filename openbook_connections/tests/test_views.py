# Create your tests here.
from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User
from faker import Faker

import logging
import json

from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_circle
from openbook_notifications.models import ConnectionConfirmedNotification, ConnectionRequestNotification, Notification

logger = logging.getLogger(__name__)

fake = Faker()


class ConnectionsAPITests(OpenbookAPITestCase):
    """
    ConnectionsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_retrieve_own_connections(self):
        """
        should be able to retrieve own connections and return 200
        """
        user = make_user()
        auth_token = user.auth_token.key
        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle = mixer.blend(Circle, creator=user)

        users_to_connect = mixer.cycle(5).blend(User)
        user_to_connect_ids = [user_to_connect.pk for user_to_connect in users_to_connect]

        for user_to_connect in users_to_connect:
            user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circle.pk])

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_connections = json.loads(response.content)

        self.assertEqual(len(response_connections), len(users_to_connect))

        for response_connection in response_connections:
            target_user = response_connection.get('target_user')
            target_user_id = target_user.get('id')
            self.assertIn(target_user_id, user_to_connect_ids)

    def _get_url(self):
        return reverse('connections')


class ConnectAPITests(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_connect(self):
        """
        should be able to connect with another user on an specific circle, add the connections circle and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.is_connected_with_user_in_circle(user_to_connect, circle_to_connect))
        self.assertTrue(
            user.is_connected_with_user_with_id_in_circle_with_id(user_to_connect.pk, user.connections_circle_id))

    def test_connect_autofollows(self):
        """
        should autofollow the user it attempts to connect with
        """
        user = make_user()

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        self.client.post(url, data, **headers, format='multipart')

        self.assertTrue(user.is_following_user_with_id(user_to_connect.pk))

    def test_connect_in_multiple_circles(self):
        """
        should be able to connect another user on multiple circles and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        amount_of_circles = 4
        circles_to_connect_ids = []

        for i in range(amount_of_circles):
            circle_to_connect = mixer.blend(Circle, creator=user)
            circles_to_connect_ids.append(circle_to_connect.pk)

        user_to_connect = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_circles_ids = ','.join(map(str, circles_to_connect_ids))

        data = {
            'username': user_to_connect.username,
            'circles_ids': stringified_circles_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for circle_id in circles_to_connect_ids:
            self.assertTrue(user.is_connected_with_user_with_id_in_circle_with_id(user_to_connect, circle_id))

        self.assertTrue(
            user.is_connected_with_user_with_id_in_circle_with_id(user_to_connect.pk, user.connections_circle_id))

    def test_cannot_connect_with_existing_connection(self):
        """
        should not be able to connect with a user already connected with and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circle_to_connect.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_connect_in_world_circle(self):
        """
        should not be able to connect with a user in the world circle and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        user_to_connect = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_connect.username,
            'circles_ids': Circle.get_world_circle()
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_connect_should_create_connection_request_notification(self):
        """
        should create a connection request notification when trying to connect with an user
        """
        user = make_user()

        user_to_connect = make_user()
        circle_to_connect = mixer.blend(Circle, creator=user)

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username,
            'circles_ids': [circle_to_connect.pk]
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(ConnectionRequestNotification.objects.filter(notification__owner_id=user_to_connect.pk,
                                                                     connection_requester_id=user.pk).exists())

    def test_cannot_connect_with_private_visibility_user_without_following(self):
        """
        should not be able to connect with a private visibility user without previously following and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_connect.is_connected_with_user_with_id(user_id=user.pk))

    def test_can_connect_with_private_visibility_user_previously_following(self):
        """
        should be able to connect with a private visibility user having previously followed it and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        user.create_follow_request_for_user(user=user_to_connect)
        user_to_connect.approve_follow_request_from_user(user=user)

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_connect.is_connected_with_user_with_id(user_id=user.pk))

    def test_can_connect_with_okuna_visibility_without_previously_following(self):
        """
        should be able to connect with a okuna visibility without having previously followed the person and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user(visibility=User.VISIBILITY_TYPE_PUBLIC)

        data = {
            'username': user_to_connect.username,
            'circles_ids': circle_to_connect.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_connect.is_connected_with_user_with_id(user_id=user.pk))

    def _get_url(self):
        return reverse('connect-with-user')


class DisconnectAPITest(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_disconnect(self):
        """
        should be able to disconnect from a user and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circle_to_connect.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_connect.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.is_connected_with_user_in_circle(user_to_connect, circle_to_connect))

    def test_disconnect_unfollows(self):
        """
        should automatically unfollow a user it disconnects from
        """
        user = make_user()

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circle_to_connect.pk])
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username
        }

        url = self._get_url()

        self.client.post(url, data, **headers, format='multipart')

        self.assertFalse(user.is_following_user_with_id(user_to_connect.pk))

    def test_cannot_disconnect_from_unexisting_connection(self):
        """
        should not be able to disconnect from an unexisting connection and return 400
        """
        user = make_user()

        not_connected_user = make_user()

        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_connected_user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.is_connected_with_user(not_connected_user))

    def test_disconnect_should_delete_own_connection_confirmed_notification(self):
        """
        should delete own connection confirmed notification when the user disconnects from a user
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        connection_confirmed_notification = ConnectionConfirmedNotification.objects.get(
            connection_confirmator=user_to_connect,
            notification__owner=user)
        notification = Notification.objects.get(notification_type=Notification.CONNECTION_CONFIRMED,
                                                object_id=connection_confirmed_notification.pk)

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            ConnectionConfirmedNotification.objects.filter(pk=connection_confirmed_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_disconnect_should_delete_foreign_connection_confirmed_notification(self):
        """
        should delete foreign connection confirmed notification when the user disconnects from a user
        """
        user = make_user()
        user_to_connect = make_user()

        user_to_connect.connect_with_user_with_id(user.pk)
        user.confirm_connection_with_user_with_id(user_to_connect.pk)

        connection_confirmed_notification = ConnectionConfirmedNotification.objects.get(connection_confirmator=user,
                                                                                        notification__owner=user_to_connect)
        notification = Notification.objects.get(notification_type=Notification.CONNECTION_CONFIRMED,
                                                object_id=connection_confirmed_notification.pk)

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            ConnectionConfirmedNotification.objects.filter(pk=connection_confirmed_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_disconnect_from_unconfirmed_connection_should_delete_own_connection_request_notification(self):
        """
        should delete own connection request notification when the user disconnects from a unconfirmed connection
        """
        user = make_user()
        user_to_connect = make_user()

        user_to_connect.connect_with_user_with_id(user.pk)

        connection_request_notification = ConnectionRequestNotification.objects.get(
            connection_requester=user_to_connect)
        notification = Notification.objects.get(owner=user,
                                                notification_type=Notification.CONNECTION_REQUEST,
                                                object_id=connection_request_notification.pk)

        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user_to_connect.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            ConnectionRequestNotification.objects.filter(pk=connection_request_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def _get_url(self):
        return reverse('disconnect-from-user')


class UpdateConnectionAPITest(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_update_connection(self):
        """
        should be able to update an own connection and return 200
        """
        user = make_user()

        auth_token = user.auth_token.key

        circle_to_connect = mixer.blend(Circle, creator=user)
        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circle_to_connect.pk])

        new_circle = mixer.blend(Circle, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_connect.username,
            'circles_ids': new_circle.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.is_connected_with_user_in_circle(user_to_connect, new_circle))
        self.assertFalse(user.is_connected_with_user_in_circle(user_to_connect, circle_to_connect))
        self.assertTrue(
            user.is_connected_with_user_with_id_in_circle_with_id(user_to_connect.pk, user.connections_circle_id))

    def test_update_connect_multiple_circles(self):
        """
        should be able to update an own connect of multiple circles and return 200
        """
        user = make_user()
        user_to_connect = make_user()

        initial_circle_to_connect_in = mixer.blend(Circle, creator=user)

        user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[initial_circle_to_connect_in.pk])

        auth_token = user.auth_token.key

        amount_of_circles = 4
        new_circles_to_connect_ids = []

        for i in range(amount_of_circles):
            circle_to_connect = mixer.blend(Circle, creator=user)
            new_circles_to_connect_ids.append(circle_to_connect.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_circles_ids = ','.join(map(str, new_circles_to_connect_ids))

        data = {
            'username': user_to_connect.username,
            'circles_ids': stringified_circles_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        connection = user.get_connection_for_user_with_id(user_to_connect.pk)
        connection_circles_ids = [circle.pk for circle in connection.circles.all()]

        # Plus one because the connections circle will be there
        self.assertEqual(len(new_circles_to_connect_ids) + 1, len(connection_circles_ids))

        for circle_id in new_circles_to_connect_ids:
            self.assertIn(circle_id, connection_circles_ids)

        self.assertTrue(
            user.is_connected_with_user_with_id_in_circle_with_id(user_to_connect.pk, user.connections_circle_id))

    def test_cannot_update_unexisting_connection(self):
        """
        should not be able to update an unexisting connection and return 400
        """
        user = make_user()

        auth_token = user.auth_token.key

        not_connected_user = make_user()

        new_circle = mixer.blend(Circle, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_connected_user.username,
            'circles_ids': new_circle.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('update-connection')


class ConfirmConnectionAPITest(OpenbookAPITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_confirm_connection(self):
        """
        should be able to confirm a connection, have it automatically added to connections circle and return 200
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.is_fully_connected_with_user_with_id(user_to_connect.pk))
        self.assertTrue(user_to_connect.is_fully_connected_with_user_with_id(user.pk))

        # Check user got automatically added to connections circle
        connection = user_to_connect.get_connection_for_user_with_id(user.pk)
        self.assertTrue(connection.circles.filter(id=user_to_connect.connections_circle_id).exists())

    def test_confirm_connection_autofollows(self):
        """
        should autofollow the user it confirms the connection with
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username
        }

        url = self._get_url()

        self.client.post(url, data, **headers, format='multipart')

        self.assertTrue(user.is_following_user_with_id(user_to_connect.pk))

    def test_confirm_connection_in_circle(self):
        """
        should be able to confirm a connection in a custom circle and return 200
        """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username,
            'circles_ids': circle.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.is_fully_connected_with_user_with_id(user_to_connect.pk))
        self.assertTrue(user_to_connect.is_fully_connected_with_user_with_id(user.pk))

        connection = user_to_connect.get_connection_for_user_with_id(user.pk)
        self.assertTrue(connection.circles.filter(id=circle.pk).exists())

    def test_cannot_confirm_unexisting_connection(self):
        """
        should not be able to confirm an unexisting connection and return 400
        """
        user = make_user()

        user_to_connect = make_user()

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.is_fully_connected_with_user_with_id(user_to_connect.pk))
        self.assertFalse(user_to_connect.is_fully_connected_with_user_with_id(user.pk))

    def test_confirm_connection_should_create_connection_confirmed_notification(self):
        """
        should create a connection confirmed notification when a connection is confirmed
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ConnectionConfirmedNotification.objects.filter(notification__owner_id=user.pk,
                                                                       connection_confirmator_id=user_to_connect.pk).exists())

    def test_confirm_connection_should_delete_connection_request_notification(self):
        """
        should delete the connection request notification once the connection is confirmed
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        headers = make_authentication_headers_for_user(user_to_connect)

        data = {
            'username': user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(ConnectionRequestNotification.objects.filter(notification__owner_id=user_to_connect.pk,
                                                                      connection_requester_id=user_to_connect.pk).exists())

    def _get_url(self):
        return reverse('confirm-connection')
