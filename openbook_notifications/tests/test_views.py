import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_notification
from openbook_notifications.models import Notification

fake = Faker()


class NotificationsAPITests(APITestCase):
    """
    NotificationsAPI
    """

    def test_can_retrieve_notifications(self):
        """
        should be able to retrieve all notifications and return 200
        """
        user = make_user()

        amount_of_notifications = 5
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_notifications = json.loads(response.content)

        self.assertEqual(len(response_notifications), len(notifications_ids))

        for response_notification in response_notifications:
            response_notification_id = response_notification.get('id')
            self.assertIn(response_notification_id, notifications_ids)

    def test_can_delete_notifications(self):
        """
        should be able to delete all notifications and return 200
        """
        user = make_user()

        amount_of_notifications = 5
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Notification.objects.filter(owner=user).exists())

    def _get_url(self):
        return reverse('notifications')


class ReadNotificationsAPITests(APITestCase):
    """
    ReadNotificationsAPI
    """

    def test_should_be_able_to_read_notifications(self):
        """
        should be able to read all notifications and return 200
        """
        user = make_user()

        amount_of_notifications = 5
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(Notification.objects.filter(owner=user, read=True, id__in=notifications_ids).count() == len(
            notifications_ids))

    def _get_url(self):
        return reverse('read-notifications')
