# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User
from faker import Faker

import logging
import json

from openbook_lists.models import List
from openbook_follows.models import Follow

logger = logging.getLogger(__name__)

fake = Faker()


class FollowsAPITests(APITestCase):
    """
    FollowsAPI
    """

    def test_retrieve_own_follows(self):
        """
        should be able to retrieve own follows and return 200
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key
        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=user)

        users_to_follow = mixer.cycle(5).blend(User)
        user_to_follow_ids = [user_to_follow.pk for user_to_follow in users_to_follow]

        for user_to_follow in users_to_follow:
            user.follow_user(user_to_follow, lists_ids=[list.pk])

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_follows = json.loads(response.content)

        self.assertEqual(len(response_follows), len(users_to_follow))

        for response_follow in response_follows:
            followed_user = response_follow.get('followed_user')
            followed_user_id = followed_user.get('id')
            self.assertIn(followed_user_id, user_to_follow_ids)

    def _get_url(self):
        return reverse('follows')


class FollowAPITests(APITestCase):
    def test_follow(self):
        """
        should be able to follow another user on an specific list and return 200
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = mixer.blend(User)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.is_following_user_in_list(user_to_follow, list_to_follow))

    def test_follow_in_multiple_lists(self):
        """
        should be able to follow another user on multiple lists and return 200
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        amount_of_lists = 4
        lists_to_follow_ids = []

        for i in range(amount_of_lists):
            list_to_follow = mixer.blend(List, creator=user)
            lists_to_follow_ids.append(list_to_follow.pk)

        user_to_follow = mixer.blend(User)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_lists_ids = ','.join(map(str, lists_to_follow_ids))

        data = {
            'username': user_to_follow.username,
            'lists_ids': stringified_lists_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for list_id in lists_to_follow_ids:
            self.assertTrue(user.is_following_user_with_id_in_list_with_id(user_to_follow, list_id))

    def test_cannot_follow_with_existing_follow(self):
        """
        should not be able to follow a user already followed with and return 400
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = mixer.blend(User)

        user.follow_user(user_to_follow, lists_ids=[list_to_follow.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_follow_oneself(self):
        """
        should not be able to follow oneself and return 400
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user.username,
            'lists_ids': list_to_follow.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Follow.objects.filter(user=user, followed_user=user).count() == 0)

    def _get_url(self):
        return reverse('follow-user')


class UnfollowAPITest(APITestCase):
    def test_unfollow(self):
        """
        should be able to unfollow a user and return 200
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_unfollow = mixer.blend(User)

        user.follow_user(user_to_unfollow, lists_ids=[list_to_follow.pk])

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_unfollow.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.is_following_user_in_list(user_to_unfollow, list_to_follow))

    def test_cannot_unfollow_from_unexisting_follow(self):
        """
        should not be able to unfollow from an unexisting follow and return 400
        """
        user = mixer.blend(User)

        not_followed_user = mixer.blend(User)

        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_followed_user.username
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.is_following_user(not_followed_user))

    def _get_url(self):
        return reverse('unfollow-user')


class UpdateFollowAPITest(APITestCase):
    def test_update_follow(self):
        """
        should be able to update an own follow and return 200
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_to_follow = mixer.blend(List, creator=user)
        user_to_follow = mixer.blend(User)

        user.follow_user(user_to_follow, lists_ids=[list_to_follow.pk])

        new_list = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': user_to_follow.username,
            'lists_ids': new_list.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.is_following_user_in_list(user_to_follow, new_list))

    def test_update_follow_multiple_lists(self):
        """
        should be able to update an own follow of multiple lists and return 200
        """
        user = mixer.blend(User)
        user_to_follow = mixer.blend(User)

        initial_list_to_follow_in = mixer.blend(List, creator=user)

        user.follow_user(user_to_follow, lists_ids=[initial_list_to_follow_in.pk])

        auth_token = user.auth_token.key

        amount_of_lists = 4
        new_lists_to_follow_ids = []

        for i in range(amount_of_lists):
            list_to_follow = mixer.blend(List, creator=user)
            new_lists_to_follow_ids.append(list_to_follow.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        stringified_lists_ids = ','.join(map(str, new_lists_to_follow_ids))

        data = {
            'username': user_to_follow.username,
            'lists_ids': stringified_lists_ids
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow = user.get_follow_for_user_with_id(user_to_follow.pk)
        follow_lists_ids = [list.pk for list in follow.lists.all()]

        self.assertEqual(len(new_lists_to_follow_ids), len(follow_lists_ids))

        for list_id in new_lists_to_follow_ids:
            self.assertIn(list_id, follow_lists_ids)

    def test_cannot_update_unexisting_follow(self):
        """
        should not be able to update an unexisting follow and return 400
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        not_followed_user = mixer.blend(User)

        new_list = mixer.blend(List, creator=user)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'username': not_followed_user.username,
            'lists_ids': new_list.pk
        }

        url = self._get_url()

        response = self.client.post(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('update-follow')
