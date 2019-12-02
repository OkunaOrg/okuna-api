import tempfile
import uuid
from PIL import Image
from django.urls import reverse
from faker import Faker
from unittest import mock
from django.core import mail
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from django.contrib.auth import authenticate
from openbook_auth.models import User, UserProfile
from rest_framework.authtoken.models import Token

import logging
import json

from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_badge, make_authentication_headers_for_user
from openbook_invitations.models import UserInvite

fake = Faker()

logger = logging.getLogger(__name__)


class RegistrationAPITests(OpenbookAPITestCase):
    """
    RegistrationAPI
    """

    def test_token_required(self):
        """
        should return 400 if the token is not present
        """
        url = self._get_url()
        data = {'name': 'Joel Hernandez', 'password': 'secretPassword123',
                'is_of_legal_age': 'true', 'email': 'user@email.com', 'are_guidelines_accepted': True}
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
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token,
                              'are_guidelines_accepted': True}
        self.client.post(url, first_request_data, format='multipart')
        second_request_data = {'name': 'Juan Taramera', 'email': 'joel2@open-book.org',
                               'password': 'woahpassword123', 'is_of_legal_age': 'true', 'token': token,
                               'are_guidelines_accepted': True}
        response = self.client.post(url, second_request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_should_be_valid(self):
        """
        should return 400 if token is invalid.
        """
        url = self._get_url()
        token = uuid.uuid4()
        first_request_data = {'name': 'Joel Hernandez', 'email': 'joel@open-book.org',
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token,
                              'are_guidelines_accepted': True}
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
                'are_guidelines_accepted': True,
                'token': token
            }
            response = self.client.post(url, data, format='multipart')
            parsed_response = json.loads(response.content)
            self.assertIn('name', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_username(self):
        """
        should return 400 if the username is not valid
        """
        url = self._get_url()
        invalid_usernames = ('joel<;<', '<>', ' shantanu space ', 'greater_than_30_characters_username_is_not_valid',)
        token = self._make_user_invite_token()
        for username in invalid_usernames:
            data = {
                'username': username,
                'name': 'Shantanu',
                'email': 'user@mail.com',
                'password': 'secretPassword123',
                'is_of_legal_age': 'true',
                'are_guidelines_accepted': True,
                'token': token
            }
            response = self.client.post(url, data, format='multipart')
            parsed_response = json.loads(response.content)
            self.assertIn('username', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_required(self):
        """
        should return 400 if the name is not present
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'email': 'user@mail.com', 'password': 'secretPassword123',
                'is_of_legal_age': 'true', 'token': token, 'are_guidelines_accepted': True}
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
                'is_of_legal_age': 'true', 'token': token, 'are_guidelines_accepted': True}
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
                'password': 'secretPassword123', 'token': token, 'are_guidelines_accepted': True}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_is_of_legal_age_true_required(self):
        """
        should return 400 if the is_of_legal_age is false
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'email': 'user@mail.com',
                'password': 'secretPassword123', 'is_of_legal_age': 'false', 'token': token,
                'are_guidelines_accepted': True}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_are_guidelines_accepted_required(self):
        """
        should return 400 if are_guidelines_accepted is not present
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'email': 'user2@mail.com',
                'password': 'secretPassword123', 'token': token, 'is_of_legal_age': True}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_are_guidelines_accepted_true_required(self):
        """
        should return 400 if are_guidelines_accepted is false
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        data = {'name': 'Joel Hernandez', 'email': 'user@mail.com',
                'password': 'secretPassword123', 'is_of_legal_age': True, 'are_guidelines_accepted': False,
                'token': token}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_taken(self):
        """
        should return 400 if email is taken.
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = 'joel@open-book.org'
        first_request_data = {'name': 'Joel Hernandez', 'email': email,
                              'password': 'secretPassword123', 'is_of_legal_age': 'true', 'token': token,
                              'are_guidelines_accepted': True}
        self.client.post(url, first_request_data, format='multipart')
        token2 = self._make_user_invite_token()
        second_request_data = {'name': 'Juan Taramera', 'email': email,
                               'password': 'woahpassword123', 'is_of_legal_age': 'true', 'token': token2,
                               'are_guidelines_accepted': True}
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
                              'password': 'secretPassword123', 'is_of_legal_age': True, 'token': token,
                              'are_guidelines_accepted': True}
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
                        'password': 'secretPassword123', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True}
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
                        'password': 'secretPassword123', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True}
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
                        'password': 'secretPassword123', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True}
        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Circle.objects.count(), 1)

        user = User.objects.get(email=email)

        # Check we created the connections circle
        self.assertTrue(Circle.objects.filter(id__in=(user.connections_circle_id,)).count() == 1)

        # Check we have a circles related manager
        self.assertTrue(hasattr(user, 'circles'))

    def test_user_guidelines_are_accepted(self):
        """
        should create a User model instance
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = fake.email()
        first_request_data = {'name': 'Joel Hernandez', 'email': email,
                              'password': 'secretPassword123', 'is_of_legal_age': True, 'token': token,
                              'are_guidelines_accepted': True}
        response = self.client.post(url, first_request_data, format='multipart')
        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        username = parsed_response['username']

        user = User.objects.get(username=username)
        self.assertTrue(user.are_guidelines_accepted)

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
                        'password': 'secretPassword123', 'is_of_legal_age': 'true', 'avatar': tmp_file,
                        'are_guidelines_accepted': True}
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
                'password': 'askdnaoisd!', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True
            },
            {
                'token': token2, 'name': 'Terry Crews', 'email': 'terry@oldsp.ie',
                'password': 'secretPassword123', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True
            },
            {
                'token': token3, 'name': 'Mike Johnson', 'email': 'mike@chowchow.com',
                'password': 'OhGoDwEnEEdFixTurES!', 'is_of_legal_age': 'true', 'are_guidelines_accepted': True
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


class VerifyRegistrationTokenAPITests(OpenbookAPITestCase):
    """
    VerifyRegistrationToken API
    """
    def test_should_reject_invalid_token(self):
        """
        should return 400 if token is invalid.
        """
        url = self._get_url()
        token = uuid.uuid4()
        request_data = {'token': token}
        response = self.client.post(url, request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_should_accept_valid_token(self):
        """
        should return 202 if token is valid.
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        request_data = {'token': token}
        response = self.client.post(url, request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_should_reject_expired_token(self):
        """
        should return 400 if token already has been used to create an account.
        """
        url = self._get_url()
        token = self._make_user_invite_token()
        email = fake.email()
        name = fake.user_name()
        password = fake.password()
        user_invite = UserInvite.get_invite_for_token(token=token)
        username = user_invite.username
        if not user_invite.username:
            username = User.get_temporary_username(email)

        # create a user
        new_user = User.create_user(username=username, email=email, password=password, name=name, avatar=None,
                         is_of_legal_age=True, badge=user_invite.badge, are_guidelines_accepted=True)
        user_invite.created_user = new_user
        user_invite.save()

        request_data = {'token': token}
        response = self.client.post(url, request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('verify-register-token')

    def _make_user_invite_token(self):
        user_invite = UserInvite.create_invite(email=fake.email())
        return user_invite.token


class RequestPasswordResetAPITests(OpenbookAPITestCase):

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
        self.assertEqual(email_message.subject, 'Reset your password for Okuna')

    def _get_url(self):
        return reverse('request-password-reset')


class VerifyResetPasswordAPITests(OpenbookAPITestCase):

    def test_can_update_password_with_valid_token(self):
        """
        Should update password with valid token
        """
        user = make_user()
        old_password = user.password
        user_email = user.email
        username = user.username
        url = self._get_url()

        password_reset_token = user.request_password_reset()
        new_password = 'testing12345'
        request_data = {
            'new_password': new_password,
            'token': password_reset_token,
        }

        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # cannot authenticate with old password
        user = authenticate(username=username, password=old_password)
        self.assertTrue(user is None)
        # can authenticate with new password
        user_new = authenticate(username=username, password=new_password)
        self.assertEqual(user_new.email, user_email)

    def test_cannot_update_password_with_invalid_token(self):
        """
        Should not update password with invalid token for email
        """
        user = make_user()
        old_password = user.password
        user_email = user.email

        url = self._get_url()

        new_password = 'testing12345'
        request_data = {
            'new_password': new_password,
            'token': fake.text()
        }

        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_db = User.objects.get(email=user_email)
        self.assertEqual(user_db.password, old_password)

    def test_cannot_update_password_without_providing_new_password(self):
        """
        Should not update password without a new password
        """
        user = make_user()
        old_password = user.password
        user_email = user.email

        url = self._get_url()

        password_reset_token = user.request_password_reset()
        request_data = {
            'token': password_reset_token
        }

        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_db = User.objects.get(email=user_email)
        self.assertEqual(user_db.password, old_password)

    def test_cannot_update_password_without_providing_token(self):
        """
        Should not update password without providing token
        """
        user = make_user()
        old_password = user.password
        user_email = user.email

        url = self._get_url()

        new_password = 'testing12345'
        request_data = {
            'new_password': new_password,
        }

        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_db = User.objects.get(email=user_email)
        self.assertEqual(user_db.password, old_password)

    def test_updating_password_with_valid_token_resets_auth_token(self):
        """
        updating the password with a valid token should reset the auth token
        """
        user = make_user()
        original_auth_token_key = user.auth_token.key
        user_email = user.email
        username = user.username
        url = self._get_url()

        password_reset_token = user.request_password_reset()
        new_password = 'testing12345'
        request_data = {
            'new_password': new_password,
            'token': password_reset_token,
        }

        response = self.client.post(url, request_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # can authenticate with new password
        user = authenticate(username=username, password=new_password)
        self.assertEqual(user.email, user_email)

        self.assertNotEqual(original_auth_token_key, user.auth_token.key)
        self.assertFalse(Token.objects.filter(key=original_auth_token_key).exists())

    def _get_url(self):
        return reverse('verify-reset-password')


class UsernameCheckAPITests(OpenbookAPITestCase):
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


class EmailCheckAPITests(OpenbookAPITestCase):
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


class LoginAPITests(OpenbookAPITestCase):
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


class VerifyChangeEmailAPITests(OpenbookAPITestCase):

    def test_can_verify_email_token_successfully(self):
        """
        should be able to verify the authenticated user email with token
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_email = fake.email()
        token = user.request_email_update(new_email)

        response = self.client.post(self._get_verify_email_url(), {'token': token}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.email == new_email)

    def test_cannot_verify_email_with_other_user_id(self):
        """
        should not be able to verify the authenticated user email with foreign user token for same email
        """
        user = make_user()
        foreign_user = make_user()
        original_email = user.email
        new_email = fake.email()
        foreign_token = foreign_user.request_email_update(new_email)

        user.request_email_update(new_email)
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(self._get_verify_email_url(), {'token': foreign_token}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user.refresh_from_db()

        # user email should not have changed
        self.assertTrue(user.email == original_email)

    def _get_verify_email_url(self):
        return reverse('email-verify')
