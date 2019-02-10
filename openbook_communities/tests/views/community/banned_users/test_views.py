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


class CommunityBannedUsersAPITest(APITestCase):
    def test_cannot_retrieve_banned_users_of_private_community(self):
        """
        should not be able to retrieve the banned users of a private community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')
        community_name = community.name

        user_to_ban = make_user()
        other_user.ban_user_with_username_from_community_with_name(username=user_to_ban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_banned_users_of_public_community(self):
        """
        should not be able to retrieve the banned users of a public community
        :return:
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user_to_ban = make_user()
        other_user.ban_user_with_username_from_community_with_name(username=user_to_ban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_banned_users_of_community_member_of(self):
        """
        should not be able to retrieve the banned users of a community member of
        :return:
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)

        user_to_ban = make_user()
        other_user.ban_user_with_username_from_community_with_name(username=user_to_ban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_banned_users_of_community_if_admin(self):
        """
        should be able to retrieve the banned users of a community if is an admin
        :return:
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        amount_of_banned_users = 5
        banned_users_ids = []

        for i in range(0, amount_of_banned_users):
            community_member = make_user()
            other_user.ban_user_with_username_from_community_with_name(username=community_member.username,
                                                                       community_name=community_name)
            banned_users_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_banned_users = json.loads(response.content)

        self.assertEqual(len(response_banned_users), len(banned_users_ids))

        for response_banned_user in response_banned_users:
            response_member_id = response_banned_user.get('id')
            self.assertIn(response_member_id, banned_users_ids)

    def test_can_retrieve_banned_users_of_community_if_mod(self):
        """
        should be able to retrieve the banned users of a community if is a moderator
        :return:
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        amount_of_banned_users = 5
        banned_users_ids = []

        for i in range(0, amount_of_banned_users):
            community_member = make_user()
            other_user.ban_user_with_username_from_community_with_name(username=community_member.username,
                                                                       community_name=community_name)
            banned_users_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_banned_users = json.loads(response.content)

        self.assertEqual(len(response_banned_users), len(banned_users_ids))

        for response_banned_user in response_banned_users:
            response_member_id = response_banned_user.get('id')
            self.assertIn(response_member_id, banned_users_ids)

    def _get_url(self, community_name):
        return reverse('community-banned-users', kwargs={
            'community_name': community_name
        })
