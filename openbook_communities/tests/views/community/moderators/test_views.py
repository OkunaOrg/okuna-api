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


class CommunityModeratorsAPITest(OpenbookAPITestCase):

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
        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        amount_of_moderators = 5
        moderators_ids = [
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
        should be able to retrieve the community moderators if user is moderator of community
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

    def test_cant_get_community_moderators_if_banned(self):
        """
        should not be able to retrieve the community moderators if user has been banned from community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)
        community_name = community.name

        user.join_community_with_name(community_name)
        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)
        amount_of_moderators = 5

        for i in range(0, amount_of_moderators):
            community_member = make_user()
            community_member.join_community_with_name(community_name)
            community_owner.add_moderator_with_username_to_community_with_name(username=community_member,
                                                                               community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_logs_community_moderator_added(self):
        """
        should create a log when community moderator was added
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')

        moderator_to_add = make_user()
        moderator_to_add.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)
        self.client.put(url, {
            'username': moderator_to_add.username
        }, **headers)

        self.assertTrue(community.logs.filter(action_type='AM',
                                              source_user=user,
                                              target_user=moderator_to_add).exists())

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
        should not be able to add a community moderator if user is just a member of community
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
        should not be able to add a community moderator if user is not even a member of community
        """
        user = make_user()
        other_user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user, type='P')

        user_to_make_moderator = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_moderator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            user_to_make_moderator.is_moderator_of_community_with_name(community_name=community.name))

    def test_cant_add_community_moderator_if_admin(self):
        """
        should not be able to add a community moderator if the user is already an admin
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')

        user_to_make_moderator = make_user()
        user_to_make_moderator.join_community_with_name(community_name=community.name)
        user.add_administrator_with_username_to_community_with_name(username=user_to_make_moderator.username,
                                                                    community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, {
            'username': user_to_make_moderator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(
            user_to_make_moderator.is_moderator_of_community_with_name(community_name=community.name))

    def _get_url(self, community_name):
        return reverse('community-moderators', kwargs={
            'community_name': community_name
        })


class CommunityModeratorAPITest(OpenbookAPITestCase):
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

    def test_logs_community_moderator_removed(self):
        """
        should create a log when community moderator was removed
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')

        moderator_to_remove = make_user()
        moderator_to_remove.join_community_with_name(community_name=community.name)
        user.add_moderator_with_username_to_community_with_name(username=moderator_to_remove.username,
                                                                community_name=community.name)

        url = self._get_url(community_name=community.name, username=moderator_to_remove.username)
        self.client.delete(url, **headers)

        self.assertTrue(community.logs.filter(action_type='RM',
                                              source_user=user,
                                              target_user=moderator_to_remove).exists())

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
            moderator_to_remove.is_moderator_of_community_with_name(community_name=community.name))

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
            moderator_to_remove.is_moderator_of_community_with_name(community_name=community.name))

    def _get_url(self, community_name, username):
        return reverse('community-moderator', kwargs={
            'community_name': community_name,
            'community_moderator_username': username
        })


class SearchCommunityModeratorsAPITests(OpenbookAPITestCase):
    """
    SearchCommunityModeratorsAPITests
    """

    def test_can_search_community_moderators_by_name(self):
        """
        should be able to search for community moderators by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_moderators_to_search_for = 5

        for i in range(0, amount_of_community_moderators_to_search_for):
            moderator = make_user()
            moderator.join_community_with_name(community_name=community.name)
            user.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                    community_name=community.name)
            moderator_name = moderator.profile.name
            amount_of_characters_to_query = random.randint(1, len(moderator_name))
            query = moderator_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_moderators = json.loads(response.content)
            response_moderators_count = len(response_moderators)
            if response_moderators_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_moderators_count, 1)
                retrieved_moderator = response_moderators[0]
                self.assertEqual(retrieved_moderator['id'], moderator.id)
            else:
                # Our community creator was retrieved too
                for response_moderator in response_moderators:
                    response_moderator_id = response_moderator['id']
                    self.assertTrue(
                        response_moderator_id == moderator.id or response_moderator_id == user.id)
            user.remove_moderator_with_username_from_community_with_name(username=moderator.username,
                                                                         community_name=community.name)

    def test_can_search_community_moderators_by_username(self):
        """
        should be able to search for community moderators by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_moderators_to_search_for = 5

        for i in range(0, amount_of_community_moderators_to_search_for):
            moderator = make_user()
            moderator.join_community_with_name(community_name=community.name)
            user.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                    community_name=community.name)
            moderator_username = moderator.username
            amount_of_characters_to_query = random.randint(1, len(moderator_username))
            query = moderator_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_moderators = json.loads(response.content)
            response_moderators_count = len(response_moderators)
            if response_moderators_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_moderators_count, 1)
                retrieved_moderator = response_moderators[0]
                self.assertEqual(retrieved_moderator['id'], moderator.id)
            else:
                # Our community creator was retrieved too
                for response_moderator in response_moderators:
                    response_moderator_id = response_moderator['id']
                    self.assertTrue(
                        response_moderator_id == moderator.id or response_moderator_id == user.id)

            user.remove_moderator_with_username_from_community_with_name(username=moderator.username,
                                                                         community_name=community.name)

    def _get_url(self, community_name):
        return reverse('search-community-moderators', kwargs={
            'community_name': community_name,
        })
