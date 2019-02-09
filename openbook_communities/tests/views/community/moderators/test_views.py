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
    def test_can_join_public_community(self):
        """
        should be able to join a public community and return 200
        """

    def test_cannot_join_private_community_without_invite(self):
        """
        should not be able to join a private community without an invite and return 400
        """

    def test_cannot_join_already_joined_community(self):
        """
        should not be able to join a private community without an invite
        """
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
    def test_can_invite_user_to_community_part_of(self):
        """

        """