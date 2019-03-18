# Create your tests here.
import random
import tempfile
import uuid

from urllib.parse import urlsplit  # Python 3
from PIL import Image
from django.urls import reverse
from faker import Faker
from unittest import mock
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_auth.models import User, UserProfile

import logging
import json

from openbook_auth.views import UserSettings, PasswordResetRequest
from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_user_bio, \
    make_user_location, make_user_avatar, make_user_cover, make_badge, make_fake_username
from openbook_invitations.models import UserInvite

fake = Faker()

logger = logging.getLogger(__name__)


# TODO Create a user factory to automate the creation of testing users.


class RegistrationAPITests(APITestCase):
    """
    RegistrationAPI
    """

    def test_token_required(self):
        """
        should return 400 if the token is not present
        """
        url = self._get_url()
        data = {'name': 'Joel Hernandez', 'password': 'secretPassword123',
                'is_of_legal_age': 'true', 'email': 'user@email.com'}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('token', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_can_be_used_once(self):
        """
        should return 400 if token already has been used to create an account.
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        first_request_data = {'name': 'Joel Hernandez', 'email': 'joel@open-book.org',
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token}
        self.client.post(url, first_request_data, format='multipart')
        second_request_data = {'name': 'Juan Taramera', 'email': 'joel2@open-book.org',
                               'password': 'woahpassword123', 'is_of_legal_age': 'true', 'token': token}
        response = self.client.post(url, second_request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_should_be_valid(self):
        """
        should return 400 if token is invalid.
        """
        url = self._get_url()
        token = uuid.uuid4()
        first_request_data = {'name': 'Joel Hernandez', 'email': 'joel@open-book.org',
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token}
        response = self.client.post(url, first_request_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_name(self):
        """
        should return 400 if the name is not valid
        """
        url = self._get_url()
        invalid_names = ('Joel<', '<>', '',)
        token = self._make_user_invite_token()
        for name in invalid_names:
            data = {
                'username': 'lifenautjoe',
                'name': name,
                'email': 'user@mail.com',
                'password': 'secretPassword123',
                'is_of_legal_age': 'true',
                'token': token
            }
            response = self.client.post(url, data, format='multipart')
            parsed_response = json.loads(response.content)
            self.assertIn('name', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_required(self):
        """
        should return 400 if the name is not present
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'email': 'user@mail.com', 'password': 'secretPassword123',
                'is_of_legal_age': 'true', 'token': token}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('name', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_required(self):
        """
        should return 400 if the email is not present
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'password': 'secretPassword123',
                'is_of_legal_age': 'true', 'token': token}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('email', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_is_of_legal_age_required(self):
        """
        should return 400 if the is_of_legal_age is not present
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'email': 'user2@mail.com',
                'password': 'secretPassword123', 'token': token}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('is_of_legal_age', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_is_of_legal_age_true_required(self):
        """
        should return 400 if the is_of_legal_age is false
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'email': 'user@mail.com',
                'password': 'secretPassword123', 'is_of_legal_age': 'false', 'token': token}
        response = self.client.post(url, data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('is_of_legal_age', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_taken(self):
        """
        should return 400 if email is taken.
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = 'joel@open-book.org'
        first_request_data = {'name': 'Joel Hernandez', 'email': email,
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token}
        self.client.post(url, first_request_data, format='multipart')
        token2 = self._make_user_invite_token()
        second_request_data = {'name': 'Juan Taramera', 'email': email,
                               'password': 'woahpassword123', 'is_of_legal_age': 'true', 'token': token2}
        response = self.client.post(url, second_request_data, format='multipart')
        parsed_response = json.loads(response.content)
        self.assertIn('email', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_created(self):
        """
        should create a User model instance
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = fake.email()
        first_request_data = {'name': 'Joel Hernandez', 'email': email,
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token}
        response = self.client.post(url, first_request_data, format='multipart')
        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('username', parsed_response)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.filter(email=email).exists(), True)

    def test_user_profile_is_created(self):
        """
        should create a UserProfile instance and associate it to the User instance
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = fake.email()
        request_data = {'token': token, 'name': 'Joel Hernandez', 'email': email,
                        'password': 'secretPassword123', 'is_of_legal_age': 'true'}
        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        user = User.objects.get(email=email)
        self.assertTrue(hasattr(user, 'profile'))

    def test_user_profile_has_badges(self):
        """
        should send user's badges with UserProfile instance
        """
        url = self._get_url()
        badge = make_badge()
        token = self._make_user_invite_token_with_badge(badge)
        email = fake.email()
        request_data = {'token': token, 'name': 'Joel Hernandez', 'email': email,
                        'password': 'secretPassword123', 'is_of_legal_age': 'true'}
        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        user = User.objects.get(email=email)
        self.assertTrue(hasattr(user.profile, 'badges'))
        badges = user.profile.badges.all()
        self.assertTrue(badges[0].keyword, badge.keyword)

    def test_user_circles_are_created(self):
        """
        should create the default circles instance and associate it to the User instance
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = fake.email()
        request_data = {'token': token, 'name': 'Joel Hernandez', 'email': email,
                        'password': 'secretPassword123', 'is_of_legal_age': 'true'}
        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Circle.objects.count(), 1)

        user = User.objects.get(email=email)

        # Check we created the connections circle
        self.assertTrue(Circle.objects.filter(id__in=(user.connections_circle_id,)).count() == 1)

        # Check we have a circles related manager
        self.assertTrue(hasattr(user, 'circles'))

    def test_user_avatar(self):
        """
        Should accept an avatar file and store it on the UserProfile
        """
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        email = fake.email()
        token = self._make_user_invite_token()
        request_data = {'token': token, 'name': 'Joel Hernandez', 'email': email,
                        'password': 'secretPassword123', 'is_of_legal_age': 'true', 'avatar': tmp_file}
        url = self._get_url()
        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=email)
        self.assertTrue(hasattr(user.profile, 'avatar'))

    def test_user_status(self):
        """
        Should return 201 when the user was created successfully and return its auth token.
        """
        token1 = self._make_user_invite_token()
        token2 = self._make_user_invite_token()
        token3 = self._make_user_invite_token()
        users_data = (
            {
                'token': token1, 'name': 'Joel Hernandez', 'email': 'hi@ohmy.com',
                'password': 'askdnaoisd!', 'is_of_legal_age': 'true'
            },
            {
                'token': token2, 'name': 'Terry Crews', 'email': 'terry@oldsp.ie',
                'password': 'secretPassword123', 'is_of_legal_age': 'true'
            },
            {
                'token': token3, 'name': 'Mike Johnson', 'email': 'mike@chowchow.com',
                'password': 'OhGoDwEnEEdFixTurES!', 'is_of_legal_age': 'true'
            }
        )
        url = self._get_url()
        for user_data_item in users_data:
            response = self.client.post(url, user_data_item, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            parsed_response = json.loads(response.content)
            self.assertIn('token', parsed_response)
            response_auth_token = parsed_response['token']
            user = User.objects.get(email=user_data_item['email'])
            self.assertEqual(response_auth_token, user.auth_token.key)

    def _get_url(self):
        return reverse('register-user')

    def _make_user_invite_token(self):
        user_invite = UserInvite.create_invite(email=fake.email())
        return user_invite.token

    def _make_user_invite_token_with_badge(self, badge):
        user_invite = UserInvite.create_invite(email=fake.email(), badge=badge)
        return user_invite.token


class RequestPasswordResetAPITests(APITestCase):

    def test_cannot_request_password_reset_with_invalid_username(self):
        """
        Should not be able to request password reset if no valid username exists
        """
        username = make_fake_username()
        request_data = {
            'username': username
        }
        url = self._get_url()
        with mock.patch.object(User, '_send_password_reset_email_with_token', return_value=None):
            response = self.client.post(url, request_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_request_password_reset_with_invalid_email(self):
        """
        Should not be able to request password reset if no valid email exists
        """
        email = fake.email()
        request_data = {
            'email': email
        }
        url = self._get_url()
        with mock.patch.object(User, '_send_password_reset_email_with_token', return_value=None):
            response = self.client.post(url, request_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_request_password_reset_successfully_with_valid_username(self):
        """
        Should generate request password reset token for username and send mail
        """
        user = make_user()
        request_data = {
            'username': user.username
        }

        url = self._get_url()
        response = self.client.post(url, request_data, format='multipart')
        email_message = mail.outbox[0]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(email_message.to[0], user.email)
        self.assertEqual(email_message.subject, 'Reset your password for Openbook')

    def test_request_password_reset_successfully_with_valid_email(self):
        """
        Should generate request password reset token for email  and send mail
        """
        user = make_user()
        request_data = {
            'email': user.email
        }

        url = self._get_url()
        response = self.client.post(url, request_data, format='multipart')
        email_message = mail.outbox[0]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(email_message.to[0], user.email)
        self.assertEqual(email_message.subject, 'Reset your password for Openbook')

    def _get_url(self):
        return reverse('request-password-reset')


class UsernameCheckAPITests(APITestCase):
    """
    UsernameCheckAPI
    """

    def test_username_not_taken(self):
        """
        should return status 202 if username is not taken.
        """
        username = 'lifenautjoe'
        request_data = {'username': username}
        url = self._get_url()
        response = self.client.post(url, request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_username_taken(self):
        """
        should return status 400 if the username is taken
        """
        username = 'lifenautjoe'
        User.objects.create_user(username=username, password='SuChSeCuRiTyWow!', email='lifenautjoe@mail.com')
        request_data = {'username': username}
        url = self._get_url()
        response = self.client.post(url, request_data, format='json')

        parsed_response = json.loads(response.content)

        self.assertIn('username', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_username(self):
        """
        should return 400 if the username is not a valid one
        """
        url = self._get_url()
        usernames = ('lifenau!', 'p-o-t-a-t-o', '.a!', 'dexter@', '🤷‍♂️')
        for username in usernames:
            data = {
                'username': username
            }
            response = self.client.post(url, data, format='json')
            parsed_response = json.loads(response.content)
            self.assertIn('username', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_username(self):
        """
        should return 202 if the username is a valid username
        """
        url = self._get_url()
        usernames = ('lifenautjoe', 'shantanu_123', 'm4k3l0v3n0tw4r', 'o_0')
        for username in usernames:
            data = {
                'username': username
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def _get_url(self):
        return reverse('username-check')


class EmailCheckAPITests(APITestCase):
    """
    EmailCheckAPI
    """

    def test_email_not_taken(self):
        """
        should return status 202 if email is not taken.
        """
        email = 'joel@open-book.org'
        request_data = {'email': email}
        url = self._get_url()
        response = self.client.post(url, request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_email_taken(self):
        """
        should return status 400 if the email is taken
        """
        email = 'joel@open-book.org'
        User.objects.create_user(email=email, password='SuChSeCuRiTyWow!', username='lifenautjoe')
        request_data = {'email': email}
        url = self._get_url()
        response = self.client.post(url, request_data, format='json')

        parsed_response = json.loads(response.content)

        self.assertIn('email', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email(self):
        """
        should return 400 if the email is not a valid one
        """
        url = self._get_url()
        emails = ('not-a-valid-email.com', 'fake-email.com', 'joel hernandez', 'omelette@dufromage', 'test_data!asd')
        for email in emails:
            data = {
                'email': email
            }
            response = self.client.post(url, data, format='json')
            parsed_response = json.loads(response.content)
            self.assertIn('email', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_email(self):
        """
        should return 202 if the email is a valid email
        """
        url = self._get_url()
        emails = ('joel@open-book.org', 'gerald@rivia.com', 'obi@wan.com', 'c3po@robot.me')
        for email in emails:
            data = {
                'email': email
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def _get_url(self):
        return reverse('email-check')


class LoginAPITests(APITestCase):
    """
    LoginAPI
    """

    def test_login_success(self):
        """
        should return 200 and the user token when sending correct credentials
        """
        username = 'mike_waswski'
        password = 'boo_scary!'

        user = User.objects.create_user(username=username, password=password, email='lifenautjoe@mail.com')

        url = self._get_url()

        request_data = {
            'username': username,
            'password': password
        }

        response = self.client.post(url, request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('token', parsed_response)
        response_token = parsed_response['token']
        user_token = user.auth_token

        self.assertEqual(response_token, user_token.key)

    def test_login_failure(self):
        """
        should return 401 when sending incorrect credentials
        """
        username = 'pauly_d'
        password = 'theW0rstDJEv4'

        User.objects.create_user(username=username, password=password, email='pauly@mail.com')

        url = self._get_url()

        request_data = {
            'username': username,
            'password': password + '!'
        }

        response = self.client.post(url, request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _get_url(self):
        return reverse('login-user')


class AuthenticatedUserAPITests(APITestCase):
    """
    AuthenticatedUserAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_user(self):
        """
        should return 200 and the data of the authenticated user
        """
        user = make_user()

        auth_token = user.auth_token.key

        header = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        url = self._get_url()

        response = self.client.get(url, **header)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('username', parsed_response)
        response_username = parsed_response['username']
        self.assertEqual(response_username, user.username)

    def test_can_update_user_username(self):
        """
        should be able to update the authenticated user username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_username = fake.user_name()

        data = {
            'username': new_username
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.username, new_username)

    def test_can_update_user_username_to_same_username(self):
        """
        should be able to update the authenticated user username to the same it already has and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        data = {
            'username': user.username
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.username, user.username)

    def test_cannot_update_user_username_to_taken_username(self):
        """
        should be able to update the authenticated user username to a taken username and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_b = make_user()

        data = {
            'username': user_b.username
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user.refresh_from_db()

        self.assertNotEqual(user.username, user_b.username)

    def test_can_update_user_name(self):
        """
        should be able to update the authenticated user name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_name = fake.name()

        data = {
            'name': new_name
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.name, new_name)

    def test_can_update_user_bio(self):
        """
        should be able to update the authenticated user bio and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_bio = make_user_bio()

        data = {
            'bio': new_bio
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.bio, new_bio)

    def test_can_update_user_location(self):
        """
        should be able to update the authenticated user location and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_location = make_user_location()

        data = {
            'location': new_location
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.location, new_location)

    def test_can_update_user_followers_count_visible(self):
        """
        should be able to update the authenticated user followers_count_visible and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_followers_count_visible = fake.boolean()

        data = {
            'followers_count_visible': new_followers_count_visible
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.followers_count_visible, new_followers_count_visible)

    def test_can_update_user_avatar(self):
        """
        should be able to update the authenticated user avatar and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_avatar = make_user_avatar()

        data = {
            'avatar': new_avatar
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertIsNotNone(user.profile.avatar)

    def test_can_update_user_avatar_plus_username(self):
        """
        should be able to update the authenticated user avatar and username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_avatar = make_user_avatar()
        new_username = 'paulyd97'

        data = {
            'avatar': new_avatar,
            'username': new_username
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertIsNotNone(user.profile.avatar)
        self.assertEqual(user.username, new_username)

    def test_can_delete_user_avatar(self):
        """
        should be able to delete the authenticated user avatar and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.profile.avatar = make_user_avatar()

        user.save()

        data = {
            'avatar': ''
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(not user.profile.avatar)

    def test_can_update_user_cover(self):
        """
        should be able to update the authenticated user cover and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_cover = make_user_cover()

        data = {
            'cover': new_cover
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertIsNotNone(user.profile.cover)

    def test_can_delete_user_cover(self):
        """
        should be able to delete the authenticated user cover and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.profile.cover = make_user_cover()

        user.save()

        data = {
            'cover': ''
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(not user.profile.cover)

    def test_can_delete_user_bio(self):
        """
        should be able to delete the authenticated user bio and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.profile.bio = make_user_bio()

        user.save()

        data = {
            'bio': ''
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(not user.profile.bio)

    def test_can_delete_user_location(self):
        """
        should be able to delete the authenticated user location and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.profile.location = make_user_location()

        user.save()

        data = {
            'location': ''
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(not user.profile.location)

    def test_can_delete_user_url(self):
        """
        should be able to delete the authenticated user url and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.profile.url = fake.url()

        user.save()

        data = {
            'url': ''
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(not user.profile.url)

    def test_can_update_user_url(self):
        """
        should be able to update the authenticated user url and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_url = fake.url()

        data = {
            'url': new_url
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(new_url, user.profile.url)

    def test_can_update_user_url_with_not_fully_qualified_urls(self):
        """
        should be able to update the authenticated user url with not fully qualified urls and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_url = fake.url()

        parsed_url = urlsplit(new_url)

        unfully_qualified_url = parsed_url.netloc

        data = {
            'url': unfully_qualified_url
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual('https://' + unfully_qualified_url, user.profile.url)

    def _get_url(self):
        return reverse('authenticated-user')


class AuthenticatedUserDeleteTests(APITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_delete_user_with_password(self):
        """
        should be able to delete the authenticated user with his password and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_password = fake.password()

        user.set_password(user_password)

        user.save()

        data = {
            'password': user_password
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_cant_delete_user_with_wrong_password(self):
        """
        should not be able to delete the authenticated user with a wrong password and return 401
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_password = fake.password()

        user.save()

        data = {
            'password': user_password
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_cant_delete_user_without_password(self):
        """
        should not be able to delete the authenticated user without his password and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user.save()

        url = self._get_url()

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def _get_url(self):
        return reverse('authenticated-user-delete')


class AuthenticatedUserNotificationsSettingsTests(APITestCase):
    """
    AuthenticatedUserNotificationsSettings
    """

    def test_can_retrieve_notifications_settings(self):
        """
        should be able to retrieve own notifications settings and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('id', parsed_response)
        response_id = parsed_response['id']
        self.assertEqual(response_id, user.notifications_settings.pk)

    def test_can_update_notifications_settings(self):
        """
        should be able to update notifications settings and return 200
        """
        user = make_user()
        notifications_settings = user.notifications_settings

        notifications_settings.post_comment_notifications = fake.boolean()
        notifications_settings.post_reaction_notifications = fake.boolean()
        notifications_settings.follow_notifications = fake.boolean()
        notifications_settings.connection_request_notifications = fake.boolean()
        notifications_settings.connection_confirmed_notifications = fake.boolean()
        notifications_settings.community_invite_notifications = fake.boolean()

        notifications_settings.save()

        headers = make_authentication_headers_for_user(user)

        new_post_comment_notifications = notifications_settings.post_comment_notifications
        new_post_reaction_notifications = notifications_settings.post_reaction_notifications
        new_follow_notifications = notifications_settings.follow_notifications
        new_connection_request_notifications = notifications_settings.connection_request_notifications
        new_connection_confirmed_notifications = notifications_settings.connection_confirmed_notifications
        new_community_invite_notifications = notifications_settings.community_invite_notifications

        data = {
            'post_comment_notifications': new_post_comment_notifications,
            'post_reaction_notifications': new_post_reaction_notifications,
            'follow_notifications': new_follow_notifications,
            'connection_request_notifications': new_connection_request_notifications,
            'connection_confirmed_notifications': new_connection_confirmed_notifications,
            'community_invite_notifications': new_community_invite_notifications
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications_settings.refresh_from_db()

        self.assertEqual(notifications_settings.post_comment_notifications, new_post_comment_notifications)
        self.assertEqual(notifications_settings.post_reaction_notifications, new_post_reaction_notifications)
        self.assertEqual(notifications_settings.follow_notifications, new_follow_notifications)
        self.assertEqual(notifications_settings.connection_request_notifications, new_connection_request_notifications)
        self.assertEqual(notifications_settings.community_invite_notifications, new_community_invite_notifications)
        self.assertEqual(notifications_settings.connection_confirmed_notifications,
                         new_connection_confirmed_notifications)

    def _get_url(self):
        return reverse('authenticated-user-notifications-settings')


class UserAPITests(APITestCase):
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

    def _get_url(self, user):
        return reverse('user', kwargs={
            'user_username': user.username
        })


class UsersAPITests(APITestCase):
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

        url = self._get_url()
        response = self.client.get(url, {
            'query': 'lil'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), len(lil_users))

        response_usernames = [user['username'] for user in parsed_response]

        for lil_user in lil_users:
            self.assertIn(lil_user.username, response_usernames)

    def test_can_limit_amount_of_queried_users(self):
        total_users = 10
        limited_users = 5

        for i in range(total_users):
            user = make_user()
            user.profile.name = 'John Cena'
            user.profile.save()

        url = self._get_url()
        response = self.client.get(url, {
            'query': 'john',
            'count': limited_users
        })

        parsed_reponse = json.loads(response.content)

        self.assertEqual(len(parsed_reponse), limited_users)

    def _get_url(self):
        return reverse('users')


class UserSettingsAPITests(APITestCase):
    """
    User Settings API
    """
    url = reverse('user-settings')

    def test_can_change_password_successfully(self):
        """
        should be able to update the authenticated user password and return 200
        """
        user = make_user()
        current_raw_password = user.password
        user.update_password(user.password)  # make sure hashed password is stored
        headers = make_authentication_headers_for_user(user)

        new_password = fake.password()

        data = {
            'new_password': new_password,
            'current_password': current_raw_password
        }

        response = self.client.patch(self.url, data, **headers)
        parsed_reponse = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(parsed_reponse['username'], user.username)

    def test_cannot_change_password_without_current_password(self):
        """
        should not be able to update the user password without supplying the current password
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_password = fake.password()

        data = {
            'new_password': new_password
        }

        response = self.client.patch(self.url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_password_without_correct_password(self):
        """
        should not be able to update the authenticated user password without the correct password
        """
        user = make_user()
        user.update_password(user.password)  # make sure hashed password is stored
        headers = make_authentication_headers_for_user(user)

        new_password = fake.password()

        data = {
            'new_password': new_password,
            'current_password': fake.password()  # use another fake password
        }

        response = self.client.patch(self.url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_change_password_without_new_password(self):
        """
        should not be able to update the authenticated user password without the new password
        """
        user = make_user()
        current_raw_password = user.password
        user.update_password(user.password)  # make sure hashed password is stored
        headers = make_authentication_headers_for_user(user)

        data = {
            'current_password': current_raw_password
        }

        response = self.client.patch(self.url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_email_to_existing_email(self):
        """
        should not be able to update the authenticated user email to existing email
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        data = {
            'email': user.email
        }

        with mock.patch.object(UserSettings, 'send_confirmation_email', return_value=None):
            response = self.client.patch(self.url, data, **headers)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_verify_email_url(self, token):
        return reverse('email-verify', kwargs={
            'token': token
        })

    def test_can_verify_email_token_successfully(self):
        """
        should be able to verify the authenticated user email with token
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_email = fake.email()
        token = user.request_update_email(new_email)

        response = self.client.get(self._get_verify_email_url(token), **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.email == new_email)

    def test_cant_verify_email_with_other_user_id(self):
        """
        should not be able to verify the authenticated user email with foreign user token for same email
        """
        user = make_user()
        foreign_user = make_user()
        original_email = user.email
        new_email = fake.email()
        foreign_token = foreign_user.request_update_email(new_email)

        user.request_update_email(new_email)
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(self._get_verify_email_url(foreign_token), **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user.refresh_from_db()

        self.assertFalse(user.is_email_verified)
        # user email should not have changed
        self.assertTrue(user.email == original_email)


class LinkedUsersAPITests(APITestCase):
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_linked_users(self):
        """
        should be able to retrieve the authenticated user linked users
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        linked_users_ids = []
        amount_of_followers_linked_users = 5
        amount_of_connected_linked_users = 5

        amount_of_linked_users = amount_of_connected_linked_users + amount_of_followers_linked_users

        for i in range(0, amount_of_followers_linked_users):
            linked_follower_user = make_user()
            linked_follower_user.follow_user_with_id(user.pk)
            linked_users_ids.append(linked_follower_user.pk)

        for i in range(0, amount_of_connected_linked_users):
            linked_connected_user = make_user()
            linked_connected_user.connect_with_user_with_id(user.pk)
            user.confirm_connection_with_user_with_id(linked_connected_user.pk)
            linked_users_ids.append(linked_connected_user.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_linked_users = json.loads(response.content)

        self.assertEqual(len(response_linked_users), amount_of_linked_users)

        for response_member in response_linked_users:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, linked_users_ids)

    def _get_url(self):
        return reverse('linked-users')


class SearchLinkedUsersAPITests(APITestCase):
    """
    SearchLinkedUsersAPI
    """

    def test_can_search_linked_users_by_name(self):
        """
        should be able to search for linked users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_linked_users_to_search_for = 5

        for i in range(0, amount_of_linked_users_to_search_for):
            linked_user = make_user()
            linked_user.follow_user_with_id(user.pk)

            linked_user_name = linked_user.profile.name
            amount_of_characters_to_query = random.randint(1, len(linked_user_name))
            query = linked_user_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_linked_users = json.loads(response.content)
            response_members_count = len(response_linked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_linked_users[0]

            self.assertEqual(retrieved_linked_member['id'], linked_user.id)
            linked_user.unfollow_user_with_id(user.pk)

    def test_can_search_linked_users_by_username(self):
        """
        should be able to search for linked users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_linked_users_to_search_for = 5

        for i in range(0, amount_of_linked_users_to_search_for):
            linked_user = make_user()
            linked_user.follow_user_with_id(user.pk)

            linked_user_username = linked_user.username
            amount_of_characters_to_query = random.randint(1, len(linked_user_username))
            query = linked_user_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_linked_users = json.loads(response.content)
            response_members_count = len(response_linked_users)

            self.assertEqual(response_members_count, 1)
            retrieved_linked_member = response_linked_users[0]

            self.assertEqual(retrieved_linked_member['id'], linked_user.id)
            linked_user.unfollow_user_with_id(user.pk)

    def _get_url(self):
        return reverse('search-linked-users')


