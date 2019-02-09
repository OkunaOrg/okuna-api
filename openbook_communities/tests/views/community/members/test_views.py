from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community, make_fake_post_text

logger = logging.getLogger(__name__)
fake = Faker()


class CommunityMembersAPITest(APITestCase):
    def test_can_retrieve_members_of_public_community(self):
        """
        should be able to retrieve the members of a public community
        """

    def test_cannot_retrieve_members_of_private_community(self):
        """
        should not be able to retrieve the members of a private community
        """

    def test_can_retrieve_members_of_private_community_part_of(self):
        """
        should be able to retrieve the members of a private community part of
        """

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
