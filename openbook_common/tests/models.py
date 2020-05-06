from unittest.mock import patch

from rest_framework.test import APITestCase


class OpenbookAPITestCase(APITestCase):
    def setUp(self):
        self.patcher = patch('openbook_notifications.helpers._send_notification_to_user')
        self.mock_foo = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
