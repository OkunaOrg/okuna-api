# Create your tests here.
from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User

import logging
import json

from openbook_common.models import Emoji
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_emoji, \
    make_fake_list_name
from openbook_lists.models import List

logger = logging.getLogger(__name__)
fake = Faker()


class ListsAPITests(OpenbookAPITestCase):
    """
    ListsAPI
    """

    def test_create_list(self):
        """
        should be able to create a list and return 201
        """
        user = make_user()

        auth_token = user.auth_token.key

        list_emoji = mixer.blend(Emoji)

        list_name = fake.name()
        emoji_id = list_emoji.pk

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'name': list_name,
            'emoji_id': emoji_id
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(List.objects.filter(name=list_name, emoji_id=emoji_id, creator_id=user.pk).count() == 1)

    def test_retrieve_own_lists(self):
        """
        should be able to retrieve all own lists return 200
        """
        user = make_user()
        auth_token = user.auth_token.key
        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        lists = mixer.cycle(5).blend(List, creator=user)
        lists_ids = [list.pk for list in lists]

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_lists = json.loads(response.content)

        self.assertEqual(len(response_lists), len(lists_ids))

        for response_list in response_lists:
            response_list_id = response_list.get('id')
            self.assertIn(response_list_id, lists_ids)

    def _get_url(self):
        return reverse('lists')


class ListItemAPITests(OpenbookAPITestCase):
    """
    ListItemAPI
    """

    def test_retrieve_own_list(self):
        """
        should be able to retrieve an own list and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        list = mixer.blend(List, creator=user)
        list_id = list.pk

        url = self._get_url(list_id)
        response = self.client.get(url, **headers)

        response_list = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_list['id'] == list_id)

    def test_delete_own_list(self):
        """
        should be able to delete an own list and return 200
        """
        user = make_user()
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=user)
        list_id = list.pk

        url = self._get_url(list_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(List.objects.filter(id=list_id).count() == 0)

    def test_cannot_delete_other_user_list(self):
        """
        should not be able to delete another user list with and return 400
        """
        user = make_user()
        auth_token = user.auth_token.key

        other_user = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=other_user)
        list_id = list.pk

        url = self._get_url(list_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(List.objects.filter(id=list_id).count() == 1)

    def test_can_update_own_list(self):
        """
        should be able to update an own list and return 200
        """
        user = make_user()
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=user)
        list_id = list.pk

        new_list_name = 'New List Name'
        new_emoji = mixer.blend(Emoji)

        data = {
            'name': new_list_name,
            'emoji_id': new_emoji.pk
        }

        url = self._get_url(list_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(List.objects.filter(name=new_list_name, id=list_id, emoji_id=new_emoji.pk).count() == 1)

    def test_can_update_own_list_users(self):
        """
        should be able to update an own list and return 200
        """
        user = make_user()

        list = mixer.blend(List, creator=user)
        list_id = list.pk

        users_to_follow_in_list = 4

        for i in range(users_to_follow_in_list):
            user_to_follow = make_user()
            user.follow_user_with_id(user_to_follow.pk, lists_ids=[list_id])

        new_users_to_follow_in_list_amount = 2
        new_users_to_follow_in_list = []
        new_users_to_follow_in_list_usernames = []

        for i in range(new_users_to_follow_in_list_amount):
            user_to_follow = make_user()
            new_users_to_follow_in_list.append(user_to_follow)
            new_users_to_follow_in_list_usernames.append(user_to_follow.username)

        data = {
            'usernames': ','.join(map(str, new_users_to_follow_in_list_usernames))
        }

        url = self._get_url(list_id)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for new_user_to_follow in new_users_to_follow_in_list:
            self.assertTrue(user.is_following_user_with_id_in_list_with_id(new_user_to_follow.pk, list_id))

    def test_can_update_own_list_users_to_none(self):
        """
        should be able to update an own list and return 200
        """
        user = make_user()

        list = mixer.blend(List, creator=user)
        list_id = list.pk

        users_to_follow_in_list = 4

        for i in range(users_to_follow_in_list):
            user_to_follow = make_user()
            user.follow_user_with_id(user_to_follow.pk, lists_ids=[list_id])

        data = {
            'usernames': ''
        }

        url = self._get_url(list_id)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(list.users), 0)

    def test_cannot_update_other_user_list(self):
        """
        should not be able update another user list and return 400
        """
        user = make_user()
        auth_token = user.auth_token.key

        other_user = make_user()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=other_user)
        list_id = list.pk

        new_list_name = 'New List Name'
        new_emoji = mixer.blend(Emoji)

        data = {
            'name': new_list_name,
            'emoji_id': new_emoji.pk
        }

        url = self._get_url(list_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(List.objects.filter(name=new_list_name, id=list_id, emoji_id=new_emoji.pk).count() == 0)

    def _get_url(self, list_id):
        return reverse('list', kwargs={
            'list_id': list_id
        })


class ListNameCheckAPITests(OpenbookAPITestCase):
    """
    ListNameCheckAPI
    """

    def test_list_name_not_taken(self):
        """
        should return status 202 if list name is not taken.
        """

        user = make_user()

        list_name = make_fake_list_name()
        request_data = {'name': list_name}

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, request_data, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_list_name_taken(self):
        """
        should return status 400 if the listName is taken
        """
        user = make_user()
        emoji = make_emoji()

        list = user.create_list(name=make_fake_list_name(), emoji_id=emoji.pk)

        request_data = {'name': list.name}

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(url, request_data, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('list-name-check')
