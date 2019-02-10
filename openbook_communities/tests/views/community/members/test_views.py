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


class CommunityMembersAPITest(APITestCase):
    def test_can_retrieve_members_of_public_community(self):
        """
        should be able to retrieve the members of a public community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_members = 5
        community_members_ids = [
            other_user.pk
        ]

        for i in range(0, amount_of_community_members):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_members_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(community_members_ids))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, community_members_ids)

    def test_cannot_retrieve_members_of_private_community(self):
        """
        should not be able to retrieve the members of a private community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_members_of_private_community_part_of(self):
        """
        should be able to retrieve the members of a private community part of
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')
        community_name = community.name

        other_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                    community_name=community_name)
        user.join_community_with_name(community_name=community_name)

        amount_of_community_members = 5
        community_members_ids = [
            other_user.pk,
            user.pk
        ]

        for i in range(0, amount_of_community_members):
            community_member = make_user()
            other_user.invite_user_with_username_to_community_with_name(username=community_member.username,
                                                                        community_name=community_name)
            community_member.join_community_with_name(community_name=community_name)
            community_members_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(community_members_ids))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, community_members_ids)

    def _get_url(self, community_name):
        return reverse('community-members', kwargs={
            'community_name': community_name
        })


class InviteCommunityMembersAPITest(APITestCase):
    def test_can_invite_user_to_community_part_of_with_invites_enabled(self):
        """
        should be able to invite a user to join a community part of with invites enabled and return 200
        """

    def test_cannot_invite_user_to_community_part_of_with_invites_disabled(self):
        """
        should not able to invite a user to join a community part of with invites enabled and return 200
        """

    def test_can_invite_user_to_community_part_of_with_invites_disabled_if_admin(self):
        """
        should be able to invite a user to join a community when invites disabled but user is admin and return 200
        """

    def test_can_invite_user_to_community_part_of_with_invites_disabled_if_mod(self):
        """
        should be able to invite a user to join a community when invites disabled but user is mod and return 200
        """

    def _get_url(self, community_name):
        return reverse('community-invites', kwargs={
            'community_name': community_name
        })


class JoinCommunityAPITest(APITestCase):
    def test_can_join_public_community(self):
        """
        should be able to join a public community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.is_member_of_community_with_name(community_name=community.name))

    def test_can_join_private_community_with_invite(self):
        """
        should be able to join a private community with an invite and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')

        other_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                    community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.is_member_of_community_with_name(community_name=community.name))

    def test_cannot_join_private_community_without_invite(self):
        """
        should not be able to join a private community without an invite and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.is_member_of_community_with_name(community_name=community.name))

    def test_cannot_join_already_joined_community(self):
        """
        should not be able to join a private community without an invite
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='O')

        user.join_community_with_name(community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.is_member_of_community_with_name(community_name=community.name))

    def _get_url(self, community_name):
        return reverse('community-join', kwargs={
            'community_name': community_name
        })
