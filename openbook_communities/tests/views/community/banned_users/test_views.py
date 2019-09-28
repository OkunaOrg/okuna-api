import random

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community

logger = logging.getLogger(__name__)
fake = Faker()


class Communitybanned_usersAPITest(OpenbookAPITestCase):
    def test_cannot_retrieve_banned_users_of_private_community(self):
        """
        should not be able to retrieve the banned users of a private community and return 400
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
        should not be able to retrieve the banned users of a public community and return 400
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
        should not be able to retrieve the banned users of a community member of and return 400
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
        should be able to retrieve the banned users of a community if is an admin and return 200
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
        should be able to retrieve the banned users of a community if is a moderator and return 200
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


class BanCommunityUserAPITest(OpenbookAPITestCase):
    def test_can_ban_user_from_community_if_mod(self):
        """
        should be able to ban user from a community if is moderator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user_to_ban.is_banned_from_community_with_name(community.name))

    def test_logs_user_banned(self):
        """
        should create a log when a community user is banned
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertTrue(community.logs.filter(action_type='B',
                                              source_user=user,
                                              target_user=user_to_ban).exists())

    def test_cant_ban_user_from_community_if_already_banned(self):
        """
        should not be able to ban user from a community if is already banned and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')
        community_name = community.name

        user_to_ban = make_user()
        user.ban_user_with_username_from_community_with_name(username=user_to_ban.username,
                                                             community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user_to_ban.is_banned_from_community_with_name(community.name))

    def test_can_ban_user_from_community_if_admin(self):
        """
        should be able to ban user from a community if is admin and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user_to_ban.is_banned_from_community_with_name(community.name))

    def test_cant_ban_user_from_community_if_member(self):
        """
        should not be able to ban user from a community if is member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_ban.is_banned_from_community_with_name(community.name))

    def test_cant_ban_user_from_community(self):
        """
        should not be able to ban user from a community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_ban.is_banned_from_community_with_name(community.name))

    def test_ban_user_makes_it_no_longer_a_member_of_community(self):
        """
        should remove membership of a user when banned from a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_ban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_ban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user_to_ban.is_member_of_community_with_name(community_name))

    def _get_url(self, community_name):
        return reverse('community-ban-user', kwargs={
            'community_name': community_name
        })


class UnbanCommunityUserAPITest(OpenbookAPITestCase):
    def test_can_unban_user_from_community_if_mod(self):
        """
        should be able to unban user from a community if is moderator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_unban = make_user()

        other_user.ban_user_with_username_from_community_with_name(username=user_to_unban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user_to_unban.is_banned_from_community_with_name(community.name))

    def test_logs_user_unbanned(self):
        """
        should create a log when a community user is unbanned
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_unban = make_user()

        other_user.ban_user_with_username_from_community_with_name(username=user_to_unban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertTrue(community.logs.filter(action_type='U',
                                              source_user=user,
                                              target_user=user_to_unban).exists())

    def test_cant_unban_user_from_community_if_already_banned(self):
        """
        should not be able to unban user from a community if is not banned and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_unban = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_unban.is_banned_from_community_with_name(community.name))

    def test_can_unban_user_from_community_if_admin(self):
        """
        should be able to unban user from a community if is admin and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)
        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        user_to_unban = make_user()

        other_user.ban_user_with_username_from_community_with_name(username=user_to_unban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user_to_unban.is_banned_from_community_with_name(community.name))

    def test_cant_unban_user_from_community_if_member(self):
        """
        should not be able to unban user from a community if is member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user.join_community_with_name(community_name)

        user_to_unban = make_user()

        other_user.ban_user_with_username_from_community_with_name(username=user_to_unban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user_to_unban.is_banned_from_community_with_name(community.name))

    def test_cant_ban_user_from_community(self):
        """
        should not be able to ban user from a community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        user_to_unban = make_user()

        other_user.ban_user_with_username_from_community_with_name(username=user_to_unban.username,
                                                                   community_name=community_name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_unban.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user_to_unban.is_banned_from_community_with_name(community.name))

    def _get_url(self, community_name):
        return reverse('community-unban-user', kwargs={
            'community_name': community_name
        })


class SearchCommunityBannedUsersAPITests(OpenbookAPITestCase):
    """
    SearchCommunityBannedUsersAPITests
    """

    def test_can_search_community_banned_users_by_name(self):
        """
        should be able to search for community banned users by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_banned_users_to_search_for = 5

        for i in range(0, amount_of_community_banned_users_to_search_for):
            banned_user = make_user()
            banned_user.join_community_with_name(community_name=community.name)
            user.ban_user_with_username_from_community_with_name(username=banned_user.username,
                                                                 community_name=community.name)
            banned_user_username = banned_user.profile.name
            amount_of_characters_to_query = random.randint(1, len(banned_user_username))
            query = banned_user_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_banned_users = json.loads(response.content)
            response_banned_users_count = len(response_banned_users)
            if response_banned_users_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_banned_users_count, 1)
                retrieved_banned_user = response_banned_users[0]
                self.assertEqual(retrieved_banned_user['id'], banned_user.id)
            else:
                # Our community creator was retrieved too
                for response_banned_user in response_banned_users:
                    response_banned_user_id = response_banned_user['id']
                    self.assertTrue(
                        response_banned_user_id == banned_user.id or response_banned_user_id == user.id)
            user.unban_user_with_username_from_community_with_name(username=banned_user.username,
                                                                   community_name=community.name)

    def test_can_search_community_banned_users_by_username(self):
        """
        should be able to search for community banned_users by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_banned_users_to_search_for = 5

        for i in range(0, amount_of_community_banned_users_to_search_for):
            banned_user = make_user()
            banned_user.join_community_with_name(community_name=community.name)
            user.ban_user_with_username_from_community_with_name(username=banned_user.username,
                                                                 community_name=community.name)
            banned_user_username = banned_user.username
            amount_of_characters_to_query = random.randint(1, len(banned_user_username))
            query = banned_user_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_banned_users = json.loads(response.content)
            response_banned_users_count = len(response_banned_users)
            if response_banned_users_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_banned_users_count, 1)
                retrieved_banned_user = response_banned_users[0]
                self.assertEqual(retrieved_banned_user['id'], banned_user.id)
            else:
                # Our community creator was retrieved too
                for response_banned_user in response_banned_users:
                    response_banned_user_id = response_banned_user['id']
                    self.assertTrue(
                        response_banned_user_id == banned_user.id or response_banned_user_id == user.id)

            user.unban_user_with_username_from_community_with_name(username=banned_user.username,
                                                                   community_name=community.name)

    def _get_url(self, community_name):
        return reverse('search-community-banned-users', kwargs={
            'community_name': community_name,
        })
