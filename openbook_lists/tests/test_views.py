# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User

import logging
import json

from openbook_common.models import Emoji
from openbook_lists.models import List

logger = logging.getLogger(__name__)


class ListsAPITests(APITestCase):
    """
    ListsAPI
    """

    def test_create_list(self):
        """
        should create a list for the authenticated user and return 201
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        list_emoji = mixer.blend(Emoji)

        list_name = 'Friends'
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
        should retrieve the lists of the authenticated user and return 200
        """
        user = mixer.blend(User)
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


class ListItemAPITests(APITestCase):
    """
    ListItemAPI
    """

    def test_delete_own_list(self):
        """
        should delete the list with the specified id and return 200
        """
        user = mixer.blend(User)
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
        should not delete the list with the specified id and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        other_user = mixer.blend(User)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        list = mixer.blend(List, creator=other_user)
        list_id = list.pk

        url = self._get_url(list_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(List.objects.filter(id=list_id).count() == 1)

    def test_can_update_own_list(self):
        """
        should update the list with the specified id and return 200
        """
        user = mixer.blend(User)
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

    def test_cannot_update_other_user_list(self):
        """
        should not update the list with the specified id and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        other_user = mixer.blend(User)

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
