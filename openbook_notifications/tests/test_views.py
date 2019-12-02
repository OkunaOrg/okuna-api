import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_notification
from openbook_notifications.models import Notification

fake = Faker()


class NotificationsAPITests(OpenbookAPITestCase):
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

    def test_can_retrieve_notifications_by_type(self):
        """
        should be able to retrieve notifications of the specified types and return 200
        """
        user = make_user()

        amount_of_notifications = len(Notification.NOTIFICATION_TYPES)
        notifications_ids = []
        valid_ids = []
        valid_types = []

        for i in range(0, amount_of_notifications):
            notification_type = Notification.NOTIFICATION_TYPES.__getitem__(i)[0]
            notification = make_notification(owner=user, notification_type=notification_type)
            notifications_ids.append(notification.pk)

            if i < 3:
                valid_types.append(notification_type)
                valid_ids.append(notification.pk)

        url = '{0}?types={1}'.format(self._get_url(), ','.join(valid_types))
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_notifications = json.loads(response.content)

        self.assertEqual(len(response_notifications), len(valid_types))

        for response_notification in response_notifications:
            response_notification_id = response_notification.get('id')
            response_notification_type = response_notification.get('notification_type')
            self.assertIn(response_notification_id, valid_ids)
            self.assertIn(response_notification_type, valid_types)

    def test_cant_retrieve_notifications_with_bad_type(self):
        """
        should return 400 if invalid a notification type is specified
        """
        user = make_user()

        url = '{0}?types={1}'.format(self._get_url(), 'AA')
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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


class ReadNotificationsAPITests(OpenbookAPITestCase):
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
        response = self.client.post(url, {}, **headers)

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

    def test_should_be_able_to_read_notifications_by_type(self):
        """
        should be able to read notifications of the specified types and return 200
        """
        user = make_user()

        amount_of_notifications = len(Notification.NOTIFICATION_TYPES)
        notifications_ids = []
        valid_ids = []
        valid_types = []

        for i in range(0, amount_of_notifications):
            notification_type = Notification.NOTIFICATION_TYPES.__getitem__(i)[0]
            notification = make_notification(owner=user, notification_type=notification_type)
            notifications_ids.append(notification.pk)

            if i < 3:
                valid_types.append(notification_type)
                valid_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, {
            'types': ','.join(valid_types)
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_ids = set(notifications_ids) - set(valid_ids)
        self.assertEqual(Notification.objects.filter(owner=user, read=True, id__in=valid_ids).count(),
                         len(valid_ids))
        self.assertEqual(Notification.objects.filter(owner=user, read=False, id__in=invalid_ids).count(),
                         len(invalid_ids))

    def test_should_not_be_able_to_read_notifications_with_bad_type(self):
        """
        should return 400 if an invalid notification type is specified
        """
        user = make_user()

        amount_of_notifications = len(Notification.NOTIFICATION_TYPES)
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, {
            'types': 'AA'
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Notification.objects.filter(owner=user, read=True, id__in=notifications_ids).count(), 0)

    def _get_url(self):
        return reverse('read-notifications')


class NotificationItemAPITests(OpenbookAPITestCase):
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


class ReadNotificationAPITests(OpenbookAPITestCase):
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


class UnreadNotificationsCountAPITests(OpenbookAPITestCase):
    """
    UnreadNotificationsCountAPI
    """

    def test_should_be_able_to_get_unread_notifications_count(self):
        """
        should be able to get all unread count notifications and return 200
        """
        user = make_user()

        amount_of_notifications = 5
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {}, **headers)

        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(parsed_response['count'] == 5)

    def test_should_be_able_to_get_unread_notifications_count_with_max_id(self):
        """
        should be able to get all unread notifications count with a max_id and return 200
        """
        user = make_user()

        amount_of_notifications = 5

        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        max_id = notifications_ids[3]

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        print(parsed_response['count'])

        self.assertTrue(parsed_response['count'] == 4)

    def test_should_be_able_to_get_unread_notifications_count_by_type(self):
        """
        should be able to get unread notifications count of the specified types and return 200
        """
        user = make_user()

        amount_of_notifications = len(Notification.NOTIFICATION_TYPES)
        notifications_ids = []
        valid_ids = []
        valid_types = []

        for i in range(0, amount_of_notifications):
            notification_type = Notification.NOTIFICATION_TYPES.__getitem__(i)[0]
            notification = make_notification(owner=user, notification_type=notification_type)
            notifications_ids.append(notification.pk)

            if i < 3:
                valid_types.append(notification_type)
                valid_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'types': ','.join(valid_types)
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(parsed_response['count'], len(valid_ids))

    def test_should_not_be_able_to_get_unread_notifications_count_with_bad_type(self):
        """
        should return 400 if an invalid notification type is specified
        """
        user = make_user()

        amount_of_notifications = len(Notification.NOTIFICATION_TYPES)
        notifications_ids = []

        for i in range(0, amount_of_notifications):
            notification = make_notification(owner=user)
            notifications_ids.append(notification.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'types': 'AA'
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
            return reverse('unread-notifications-count')
