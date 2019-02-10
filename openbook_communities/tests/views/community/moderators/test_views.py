from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community

logger = logging.getLogger(__name__)
fake = Faker()


class CommunityModeratorsAPITest(APITestCase):

    def test_can_get_community_moderators_if_admin(self):
        """
        should be able to retrieve the community moderators if user is admin of community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        amount_of_moderators = 5
        moderators_ids = [
            user.pk,
            other_user.pk
        ]

        for i in range(0, amount_of_moderators):
            community_member = make_user()
            community_member.join_community_with_name(community_name)
            other_user.add_moderator_with_username_to_community_with_name(username=community_member,
                                                                          community_name=community.name)
            moderators_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderators = json.loads(response.content)

        self.assertEqual(len(response_moderators), len(moderators_ids))

        for response_moderator in response_moderators:
            response_moderator_id = response_moderator.get('id')
            self.assertIn(response_moderator_id, moderators_ids)

    def test_can_get_community_moderators_if_mod(self):
        """
        should be able to retrieve the community moderators if user is admin of community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        amount_of_moderators = 5
        moderators_ids = [
            other_user.pk,
            user.pk
        ]

        for i in range(0, amount_of_moderators):
            community_member = make_user()
            community_member.join_community_with_name(community_name)
            other_user.add_moderator_with_username_to_community_with_name(username=community_member,
                                                                          community_name=community.name)
            moderators_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderators = json.loads(response.content)

        self.assertEqual(len(response_moderators), len(moderators_ids))

        for response_moderator in response_moderators:
            response_moderator_id = response_moderator.get('id')
            self.assertIn(response_moderator_id, moderators_ids)

    def test_can_get_community_moderators_if_member(self):
        """
        should be able to retrieve the community moderators if user is member of community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)

        amount_of_moderators = 5
        moderators_ids = [
            other_user.pk,
        ]

        for i in range(0, amount_of_moderators):
            community_member = make_user()
            community_member.join_community_with_name(community_name)
            other_user.add_moderator_with_username_to_community_with_name(username=community_member,
                                                                          community_name=community.name)
            moderators_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderators = json.loads(response.content)

        self.assertEqual(len(response_moderators), len(moderators_ids))

        for response_moderator in response_moderators:
            response_moderator_id = response_moderator.get('id')
            self.assertIn(response_moderator_id, moderators_ids)

    def test_can_add_community_moderator_if_creator(self):
        """
        should be able to add a community moderator if user is creator of community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')

        user_to_make_moderator = make_user()
        user_to_make_moderator.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_moderator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            user_to_make_moderator.is_moderator_of_community_with_name(community_name=community.name))

    def test_can_add_community_moderator_if_admin(self):
        """
        should be able to add a community moderator if user is administrator of community
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community_name=community.name)
        other_user.add_administrator_with_username_to_community_with_name(username=user,
                                                                          community_name=community.name)

        user_to_make_admnistrator = make_user()
        user_to_make_admnistrator.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_admnistrator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            user_to_make_admnistrator.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_add_community_moderator_if_mod(self):
        """
        should not be able to add a community moderator if user is moderator of community
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community_name=community.name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_make_admnistrator = make_user()
        user_to_make_admnistrator.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_admnistrator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            user_to_make_admnistrator.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_add_community_moderator_if_member(self):
        """
        should not be able to add a community moderator if user is member of community
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community_name=community.name)

        user_to_make_admnistrator = make_user()
        user_to_make_admnistrator.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_admnistrator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            user_to_make_admnistrator.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_add_community_moderator_if_not_member(self):
        """
        should not be able to add a community moderator if user is not member of community
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user_to_make_admnistrator = make_user()
        user_to_make_admnistrator.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_admnistrator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            user_to_make_admnistrator.is_moderator_of_community_with_name(community_name=community.name))

    def _get_url(self, community_name):
        return reverse('community-moderators', kwargs={
            'community_name': community_name
        })


class CommunityModeratorAPITest(APITestCase):
    def test_can_remove_community_moderator_if_admin(self):
        """
        should be able to remove a community moderator if user is admin of the community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')

        moderator_to_remove = make_user()
        moderator_to_remove.join_community_with_name(community_name=community.name)
        user.add_moderator_with_username_to_community_with_name(username=moderator_to_remove.username,
                                                                community_name=community.name)

        url = self._get_url(community_name=community.name, username=moderator_to_remove.username)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            moderator_to_remove.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_remove_community_moderator_if_also_admin(self):
        """
        should not be able to remove a community moderator if the moderator is also an admin
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community.name)
        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        url = self._get_url(community_name=community.name, username=other_user.username)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            other_user.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_remove_community_moderator_if_mod(self):
        """
        should not be able to remove a community moderator if user is moderator
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community.name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        moderator_to_remove = make_user()
        moderator_to_remove.join_community_with_name(community_name=community.name)
        other_user.add_moderator_with_username_to_community_with_name(username=moderator_to_remove.username,
                                                                      community_name=community.name)

        url = self._get_url(community_name=community.name, username=moderator_to_remove.username)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            other_user.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_remove_community_moderator_if_member(self):
        """
        should not be able to remove a community moderator if user is member
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user.join_community_with_name(community.name)

        moderator_to_remove = make_user()
        moderator_to_remove.join_community_with_name(community_name=community.name)
        other_user.add_moderator_with_username_to_community_with_name(username=moderator_to_remove.username,
                                                                      community_name=community.name)

        url = self._get_url(community_name=community.name, username=moderator_to_remove.username)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            other_user.is_moderator_of_community_with_name(community_name=community.name))

    def _get_url(self, community_name, username):
        return reverse('community-moderator', kwargs={
            'community_name': community_name,
            'community_moderator_username': username
        })
