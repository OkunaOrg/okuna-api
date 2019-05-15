import logging

from faker import Faker
from rest_framework.test import APITestCase
from openbook_auth.models import User

fake = Faker()

logger = logging.getLogger(__name__)


class UserModelTests(APITestCase):
    def test_format_email_to_common_string(self):
        """
        should format f.o.o@gmail.com to foo@gmail.com
        """
        model = User()

        actual = 'f.o.o@gmail.com'
        expected = 'foo@gmail.com'

        formatted = model.format_email_to_common_string(actual)

        self.assertEqual(expected, formatted)
