# Create your tests here.


from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_auth.models import User, UserProfile

import logging
import json

logger = logging.getLogger(__name__)


class RegistrationAPITests(APITestCase):
    """
    RegistrationAPI
    """

    def test_username_alphanumeric_and_underscores_only(self):
        """
        should only not allow usernames with non alphanumeric and underscore characters
        """
        url = self._get_url()
        usernames = ('lifenautjoe!', 'lifenautjo@', 'lifenautpoe🔒', 'lifenaut-joe', '字kasmndikasm')
        for username in usernames:
            data = {
                'username': username,
                'name': 'Miguel',
                'email': 'user@mail.com',
                'password': 'secretPassword123',
                'birth_date': '27-1-1996'
            }
            response = self.client.post(url, data, format='multipart')
            parsed_response = json.loads(response.content)
            self.assertIn('username', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_alphanumeric_and_spaces_only(self):
        """
        should only not allow usernames with non alphanumeric and underscore characters
        """
        url = self._get_url()
        names = ('Joel!', 'Joel_', 'Joel@', 'Joel ✨', 'Joel 字', 'Joel -!')
        for name in names:
            data = {
                'username': 'lifenautjoe',
                'name': name,
                'email': 'user@mail.com',
                'password': 'secretPassword123',
                'birth_date': '27-1-1996'
            }
            response = self.client.post(url, data, format='multipart')
            parsed_response = json.loads(response.content)
            self.assertIn('name', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_is_required(self):
        """
        should require a username
        """
        url = self._get_url()
        data = {'name': 'Joel', 'email': 'user@mail.com', 'password': 'secretPassword123', 'birth_date': '27-1-1996'}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('username', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_is_required(self):
        """
        should require a name
        """
        url = self._get_url()
        data = {'username': 'lifenautjoe', 'email': 'user@mail.com', 'password': 'secretPassword123',
                'birth_date': '27-1-1996'}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('name', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_is_required(self):
        """
        should require an email
        """
        url = self._get_url()
        data = {'username': 'lifenautjoe', 'name': 'Joel Hernandez', 'password': 'secretPassword123',
                'birth_date': '27-1-1996'}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('email', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_birth_date_is_required(self):
        """
        should require a birth_date
        """
        url = self._get_url()
        data = {'username': 'lifenautjoe', 'name': 'Joel Hernandez', 'email': 'user@mail.com',
                'password': 'secretPassword123'}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('birth_date', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_is_not_taken(self):
        """
        should check whether the username is not taken
        """
        url = self._get_url()
        username = 'lifenautjoe'
        first_request_data = {'username': username, 'name': 'Joel Hernandez', 'email': 'user@mail.com',
                              'password': 'secretPassword123', 'birth_date': '27-1-1996'}
        self.client.post(url, first_request_data, format='multipart')
        second_request_data = {'username': username, 'name': 'Juan Taramera', 'email': 'juan@mail.com',
                               'password': 'woahpassword123', 'birth_date': '27-1-1996'}
        response = self.client.post(url, second_request_data, format='multipart')

        parsed_response = json.loads(response.content)

        self.assertIn('username', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_is_not_taken(self):
        """
        should check whether the email is not taken
        """
        url = self._get_url()
        email = 'joel@open-book.org'
        first_request_data = {'username': 'lifenautjoe1', 'name': 'Joel Hernandez', 'email': email,
                              'password': 'secretPassword123', 'birth_date': '27-1-1996'}
        self.client.post(url, first_request_data, format='multipart')
        second_request_data = {'username': 'lifenautjoe2', 'name': 'Juan Taramera', 'email': email,
                               'password': 'woahpassword123', 'birth_date': '27-1-1996'}
        response = self.client.post(url, second_request_data, format='multipart')
        parsed_response = json.loads(response.content)

        self.assertIn('email', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_is_created(self):
        """
        should create a User model instance
        """
        url = self._get_url()
        username = 'potato123'
        first_request_data = {'username': username, 'name': 'Joel Hernandez', 'email': 'test@email.com',
                              'password': 'secretPassword123', 'birth_date': '27-1-1996'}
        response = self.client.post(url, first_request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(username=username).exists(), True)

    def test_user_profile_is_created(self):
        """
        should create a UserProfile instance and associate it to the User instance
        """
        url = self._get_url()
        username = 'vegueta968'
        first_request_data = {'username': username, 'name': 'Joel Hernandez', 'email': 'test@email.com',
                              'password': 'secretPassword123', 'birth_date': '27-1-1996'}
        response = self.client.post(url, first_request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        user = User.objects.get(username=username)
        self.assertTrue(hasattr(user, 'profile'))

    def _get_url(self):
        return reverse('register-user')
