from unittest import mock

from urllib.parse import urlsplit
from django.urls import reverse
from faker import Faker
from rest_framework import status
from mixer.backend.django import mixer

from openbook_circles.models import Circle
from openbook_common.tests.models import OpenbookAPITestCase
from openbook_auth.models import User

import logging
import json

from openbook_auth.views.authenticated_user.views import AuthenticatedUserSettings
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_user_bio, \
    make_user_location, make_user_avatar, make_user_cover, make_random_language

fake = Faker()

logger = logging.getLogger(__name__)


class AuthenticatedUserAPITests(OpenbookAPITestCase):
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

        new_followers_count_visible = not user.profile.followers_count_visible

        data = {
            'followers_count_visible': new_followers_count_visible
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.followers_count_visible, new_followers_count_visible)

    def test_can_update_user_community_posts_visible(self):
        """
        should be able to update the authenticated user community_posts_visible and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        new_community_posts_visible = not user.profile.community_posts_visible

        data = {
            'community_posts_visible': new_community_posts_visible
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.profile.community_posts_visible, new_community_posts_visible)

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

    def test_can_update_user_visibility(self):
        """
        should be able to update the authenticated user visibility and return 200
        """

        for initial_visibility in User.VISIBILITY_TYPES:
            for new_visibility in User.VISIBILITY_TYPES:
                if new_visibility == initial_visibility:
                    return
                user = make_user(visibility=initial_visibility)
                headers = make_authentication_headers_for_user(user)

                data = {
                    'visibility': new_visibility
                }

                url = self._get_url()

                response = self.client.patch(url, data, **headers)

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                user.refresh_from_db()

                self.assertEqual(user.visibility, new_visibility)

    def test_when_updating_visibility_to_public_existing_follow_requests_get_deleted(self):
        """
        when updating the visibility to public, existing follow requests should be deleted
        """
        initial_visibility = User.VISIBILITY_TYPE_PRIVATE
        new_visibility = User.VISIBILITY_TYPE_PUBLIC

        user = make_user(visibility=initial_visibility)
        headers = make_authentication_headers_for_user(user)

        user_requesting_to_follow = make_user()
        user_requesting_to_follow.create_follow_request_for_user(user=user)

        data = {
            'visibility': new_visibility
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_follow_request_from_user(user_requesting_to_follow))

    def test_when_updating_visibility_to_private_existing_connection_requests_get_deleted(self):
        """
        when updating the visibility to private, existing connection requests should be deleted
        """
        initial_visibility = User.VISIBILITY_TYPE_PUBLIC
        new_visibility = User.VISIBILITY_TYPE_PRIVATE

        user = make_user(visibility=initial_visibility)
        headers = make_authentication_headers_for_user(user)

        number_of_connection_requests = 3

        for i in range(number_of_connection_requests):
            user_requesting_to_connect = make_user()
            circle_to_connect = mixer.blend(Circle, creator=user_requesting_to_connect)
            user_requesting_to_connect.connect_with_user_with_id(user.pk, circles_ids=[circle_to_connect.pk])

        data = {
            'visibility': new_visibility
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(user.targeted_connections.count(), 0)

    def test_when_updating_visibility_to_non_private_from_non_private_existing_connection_requests_dont_get_deleted(self):
        """
        when updating the visibility from non private, to another non private, connection requests should not be deleted
        """

        for initial_visibility, name in User.VISIBILITY_TYPES:
            for new_visibility, n_name in User.VISIBILITY_TYPES:
                if initial_visibility == User.VISIBILITY_TYPE_PRIVATE or new_visibility == User.VISIBILITY_TYPE_PRIVATE:
                    return

                user = make_user(visibility=initial_visibility)
                headers = make_authentication_headers_for_user(user)

                number_of_connection_requests = 3

                for i in range(number_of_connection_requests):
                    user_requesting_to_connect = make_user()
                    circle_to_connect = mixer.blend(Circle, creator=user_requesting_to_connect)
                    user_requesting_to_connect.connect_with_user_with_id(user.pk, circles_ids=[circle_to_connect.pk])

                data = {
                    'visibility': new_visibility
                }

                url = self._get_url()

                response = self.client.patch(url, data, **headers)

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                self.assertEqual(user.targeted_connections.count(), number_of_connection_requests)

    def _get_url(self):
        return reverse('authenticated-user')


class AuthenticatedUserDeleteTests(OpenbookAPITestCase):
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
        return reverse('delete-authenticated-user')


class AuthenticatedUserNotificationsSettingsTests(OpenbookAPITestCase):
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
        notifications_settings.follow_request_notifications = fake.boolean()
        notifications_settings.follow_request_approved_notifications = fake.boolean()
        notifications_settings.connection_request_notifications = fake.boolean()
        notifications_settings.connection_confirmed_notifications = fake.boolean()
        notifications_settings.community_invite_notifications = fake.boolean()
        notifications_settings.community_new_post_notifications = fake.boolean()
        notifications_settings.user_new_post_notifications = fake.boolean()
        notifications_settings.post_comment_reply_notifications = fake.boolean()
        notifications_settings.post_comment_reaction_notifications = fake.boolean()
        notifications_settings.post_comment_user_mention_notifications = fake.boolean()
        notifications_settings.post_user_mention_notifications = fake.boolean()

        notifications_settings.save()

        headers = make_authentication_headers_for_user(user)

        new_post_comment_notifications = not notifications_settings.post_comment_notifications
        new_post_reaction_notifications = not notifications_settings.post_reaction_notifications
        new_follow_notifications = not notifications_settings.follow_notifications
        new_follow_request_notifications = not notifications_settings.follow_request_notifications
        new_follow_request_approved_notifications = not notifications_settings.follow_request_approved_notifications
        new_connection_request_notifications = not notifications_settings.connection_request_notifications
        new_connection_confirmed_notifications = not notifications_settings.connection_confirmed_notifications
        new_community_invite_notifications = not notifications_settings.community_invite_notifications
        new_community_new_post_notifications = not notifications_settings.community_new_post_notifications
        new_user_new_post_notifications = not notifications_settings.user_new_post_notifications
        new_post_comment_reaction_notifications = not notifications_settings.post_comment_reaction_notifications
        new_post_comment_reply_notifications = not notifications_settings.post_comment_reply_notifications
        new_post_comment_user_mention_notifications = not notifications_settings.post_comment_user_mention_notifications
        new_post_user_mention_notifications = not notifications_settings.post_user_mention_notifications

        data = {
            'post_comment_notifications': new_post_comment_notifications,
            'post_reaction_notifications': new_post_reaction_notifications,
            'follow_notifications': new_follow_notifications,
            'follow_request_notifications': new_follow_request_notifications,
            'follow_request_approved_notifications': new_follow_request_approved_notifications,
            'connection_request_notifications': new_connection_request_notifications,
            'connection_confirmed_notifications': new_connection_confirmed_notifications,
            'community_invite_notifications': new_community_invite_notifications,
            'community_new_post_notifications': new_community_new_post_notifications,
            'user_new_post_notifications': new_user_new_post_notifications,
            'post_comment_reply_notifications': new_post_comment_reply_notifications,
            'post_comment_reaction_notifications': new_post_comment_reaction_notifications,
            'post_comment_user_mention_notifications': new_post_comment_user_mention_notifications,
            'post_user_mention_notifications': new_post_user_mention_notifications
        }

        url = self._get_url()

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications_settings.refresh_from_db()

        self.assertEqual(notifications_settings.post_comment_notifications, new_post_comment_notifications)
        self.assertEqual(notifications_settings.post_reaction_notifications, new_post_reaction_notifications)
        self.assertEqual(notifications_settings.follow_notifications, new_follow_notifications)
        self.assertEqual(notifications_settings.follow_request_notifications, new_follow_request_notifications)
        self.assertEqual(notifications_settings.follow_request_approved_notifications,
                         new_follow_request_approved_notifications)
        self.assertEqual(notifications_settings.connection_request_notifications, new_connection_request_notifications)
        self.assertEqual(notifications_settings.community_invite_notifications, new_community_invite_notifications)
        self.assertEqual(notifications_settings.community_new_post_notifications, new_community_new_post_notifications)
        self.assertEqual(notifications_settings.user_new_post_notifications, new_user_new_post_notifications)
        self.assertEqual(notifications_settings.connection_confirmed_notifications,
                         new_connection_confirmed_notifications)
        self.assertEqual(notifications_settings.post_comment_reply_notifications,
                         new_post_comment_reply_notifications)
        self.assertEqual(notifications_settings.post_comment_reaction_notifications,
                         new_post_comment_reaction_notifications)

    def _get_url(self):
        return reverse('authenticated-user-notifications-settings')


class AuthenticatedUserSettingsAPITests(OpenbookAPITestCase):
    """
    User Settings API
    """
    url = reverse('authenticated-user-settings')

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

        with mock.patch.object(AuthenticatedUserSettings, 'send_confirmation_email', return_value=None):
            response = self.client.patch(self.url, data, **headers)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticatedUserAcceptGuidelines(OpenbookAPITestCase):
    """
    AuthenticatedUserAcceptGuidelines API
    """
    url = reverse('authenticated-user-accept-guidelines')

    def test_can_accept_guidelines(self):
        """
        should be able to accept the guidelines and return 200
        """
        user = make_user()
        user.are_guidelines_accepted = False
        user.save()
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.are_guidelines_accepted)

    def test_cant_accept_guidelines_if_aleady_accepted(self):
        """
        should not be able to accept the guidelines if already accepted and return 400
        """
        user = make_user()
        user.are_guidelines_accepted = True
        user.save()
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user.refresh_from_db()
        self.assertTrue(user.are_guidelines_accepted)


class AuthenticatedUserLanguageAPI(OpenbookAPITestCase):
    """
    AuthenticatedUserLanguageAPI API
    """

    fixtures = [
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_get_all_languages(self):
        """
        should be able to set user language and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parsed_response = json.loads(response.content)
        self.assertTrue(len(parsed_response), 25)

    def test_can_set_language(self):
        """
        should be able to set user language and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        language = make_random_language()

        response = self.client.post(self.url, {
            'language_id': language.id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.language.id, language.id)

    def test_cannot_set_invalid_language(self):
        """
        should be able to set user language and return 200
        """
        user = make_user()
        language = make_random_language()
        user.language = language
        user.save()
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(self.url, {
            'language_id': 99999
        }, **headers)

        print(response)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertTrue(user.language.id, language.id)

    url = reverse('user-language')
