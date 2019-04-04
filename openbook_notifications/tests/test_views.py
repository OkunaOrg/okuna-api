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

    def test_should_be_able_to_read_notifications_with_max_id(self):
        """
        should be able to read all notifications with a max_id and return 200
        """
        user = make_user()

        amount_of_notifications = 5

        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        max_id = notifications_ids[-3]

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, {
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(Notification.objects.filter(owner=user, read=True, id__lte=max_id).exists())

        self.assertTrue(Notification.objects.filter(owner=user, read=False, id__gt=max_id).exists())

    def _get_url(self):
        return reverse('read-notifications')


class NotificationItemAPITests(APITestCase):
    """
    NotificationItemAPI
    """

    def test_can_delete_own_notification(self):
        """
        should be able to delete an own notification and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        notification = make_notification(owner=user)
        notification_id = notification.pk

        url = self._get_url(notification_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Notification.objects.filter(id=notification_id).exists())

    def test_cannot_delete_foreign_notification(self):
        """
        should not be able to delete a foreign notification and return 200
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        notification = make_notification(owner=foreign_user)
        notification_id = notification.pk

        url = self._get_url(notification_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(Notification.objects.filter(id=notification_id).exists())

    def _get_url(self, notification_id):
        return reverse('notification', kwargs={
            'notification_id': notification_id
        })


class ReadNotificationAPITests(APITestCase):
    """
    ReadNotificationAPI
    """

    def test_can_read_own_notification(self):
        """
        should be able to read an own notification and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        notification = make_notification(owner=user)
        notification_id = notification.pk

        url = self._get_url(notification_id)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(Notification.objects.filter(id=notification_id, read=True).exists())

    def test_cannot_read_foreign_notification(self):
        """
        should not be able to read a foreign notification and return 400
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        notification = make_notification(owner=foreign_user)
        notification_id = notification.pk

        url = self._get_url(notification_id)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(Notification.objects.filter(id=notification_id, read=False).exists())

    def _get_url(self, notification_id):
        return reverse('read-notification', kwargs={
            'notification_id': notification_id
        })
