import random

from django.urls import reverse
from faker import Faker
from rest_framework import status

import logging
import json

from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community
from openbook_communities.models import Community, CommunityNotificationsSubscription
from openbook_notifications.models import CommunityInviteNotification, Notification

logger = logging.getLogger(__name__)
fake = Faker()


class CommunityMembersAPITest(OpenbookAPITestCase):
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

    def test_cannot_retrieve_members_of_community_banned_from(self):
        """
        should not be able to retrieve the community members if user has been banned from community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)
        community_name = community.name

        user.join_community_with_name(community_name)
        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_can_retrieve_members_with_max_id_and_count(self):
        """
        should be able to retrieve community members with a max id and count
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        community_members_ids = []

        amount_of_community_members = 10
        count = 5
        # +2 Because of the user & other_user
        max_id = 6 + 2

        for i in range(0, amount_of_community_members):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_members_ids.append(community_member.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, {
            'count': count,
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_members = json.loads(response.content)

        self.assertEqual(count, len(response_members))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertTrue(response_member_id < max_id)

    def test_can_filter_administrators_from_members_of_community(self):
        """
        should be able to filter the administrators from the retrieve the members of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_members = 5
        community_members_ids = []

        for i in range(0, amount_of_community_members):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_members_ids.append(community_member.pk)

        amount_of_community_administrators = 5

        for i in range(0, amount_of_community_administrators):
            community_administrator = make_user()
            community_administrator.join_community_with_name(community_name=community_name)
            other_user.add_administrator_with_username_to_community_with_name(username=community_administrator.username,
                                                                              community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, {
            'exclude': Community.EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(community_members_ids))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, community_members_ids)

    def test_can_filter_moderators_from_members_of_community(self):
        """
        should be able to filter the moderators from the retrieve the members of a community
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

        amount_of_community_moderators = 5

        for i in range(0, amount_of_community_moderators):
            community_moderator = make_user()
            community_moderator.join_community_with_name(community_name=community_name)
            other_user.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                          community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, {
            'exclude': Community.EXCLUDE_COMMUNITY_MODERATORS_KEYWORD,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(community_members_ids))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, community_members_ids)

    def test_can_filter_moderators_and_administrators_from_members_of_community(self):
        """
        should be able to filter the moderators and administrators from the retrieve the members of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_members = 5
        community_members_ids = []

        for i in range(0, amount_of_community_members):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_members_ids.append(community_member.pk)

        amount_of_community_moderators = 5

        for i in range(0, amount_of_community_moderators):
            community_moderator = make_user()
            community_moderator.join_community_with_name(community_name=community_name)
            other_user.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                          community_name=community.name)

        amount_of_community_administrators = 5

        for i in range(0, amount_of_community_administrators):
            community_moderator = make_user()
            community_moderator.join_community_with_name(community_name=community_name)
            other_user.add_administrator_with_username_to_community_with_name(username=community_moderator.username,
                                                                              community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, {
            'exclude': ','.join(
                [Community.EXCLUDE_COMMUNITY_MODERATORS_KEYWORD, Community.EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD]),
        }, **headers)

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


class InviteCommunityMembersAPITest(OpenbookAPITestCase):
    def test_can_invite_user_to_community_part_of_with_invites_enabled(self):
        """
        should be able to invite a user to join a community part of with invites enabled and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = True
        community.save()

        user.join_community_with_name(community.name)
        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def test_invite_user_to_community_creates_community_invite_notification(self):
        """
        should create an community invite notification when a user is invited to join a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = True
        community.save()

        user.join_community_with_name(community.name)
        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(CommunityInviteNotification.objects.filter(community_invite__invited_user=user_to_invite,
                                                                   community_invite__creator=user).exists())

    def test_cannot_invite_user_to_community_not_part_of_with_invites_enabled(self):
        """
        should not be able to invite a user to join a community NOT part of with invites enabled and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = True
        community.save()

        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def test_cannot_invite_user_to_community_part_of_with_invites_disabled(self):
        """
        should not able to invite a user to join a community part of with invites enabled and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = False
        community.save()

        user.join_community_with_name(community.name)
        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def test_can_invite_user_to_community_part_of_with_invites_disabled_if_admin(self):
        """
        should be able to invite a user to join a community when invites disabled but user is admin and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = False
        community.save()

        user.join_community_with_name(community.name)

        other_user.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)

        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def test_can_invite_user_to_community_part_of_with_invites_disabled_if_mod(self):
        """
        should be able to invite a user to join a community when invites disabled but user is mod and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = False
        community.save()

        user.join_community_with_name(community.name)

        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def _get_url(self, community_name):
        return reverse('community-invite', kwargs={
            'community_name': community_name
        })


class UninviteCommunityMembersAPITest(OpenbookAPITestCase):
    def test_can_uninvite_user_from_community(self):
        """
        should be able to uninvite a user from a community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = True
        community.save()

        user.join_community_with_name(community.name)
        user_to_invite = make_user()
        user.invite_user_with_username_to_community_with_name(username=user_to_invite.username,
                                                              community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertFalse(user_to_invite.is_invited_to_community_with_name(community_name=community.name))

    def test_cannot_withdraw_unexisting_invite(self):
        """
        should not be able to withdraw an unexisting invite and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community.invites_enabled = True
        community.save()

        user.join_community_with_name(community.name)
        user_to_invite = make_user()

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, {
            'username': user_to_invite.username
        }, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def _get_url(self, community_name):
        return reverse('community-uninvite', kwargs={
            'community_name': community_name
        })


class JoinCommunityAPITest(OpenbookAPITestCase):
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

    def test_join_community_with_invite_removes_community_invite_notification(self):
        """
        should able to join a private community with an invite and remove the community invite notification
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        community_invite = other_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                                       community_name=community.name)

        community_invite_notification = CommunityInviteNotification.objects.get(
            community_invite=community_invite)

        notification = Notification.objects.get(owner=user,
                                                notification_type=Notification.COMMUNITY_INVITE,
                                                object_id=community_invite_notification.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertFalse(CommunityInviteNotification.objects.filter(community_invite__invited_user=user,
                                                                    community_invite__creator=other_user).exists())

        self.assertFalse(
            CommunityInviteNotification.objects.filter(pk=community_invite_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

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


class SearchCommunityMembersAPITests(OpenbookAPITestCase):
    """
    SearchCommunityMembersAPITests
    """

    def test_can_search_community_members_by_name(self):
        """
        should be able to search for community members by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_members_to_search_for = 5

        for i in range(0, amount_of_community_members_to_search_for):
            member = make_user()
            member.join_community_with_name(community_name=community.name)
            member_name = member.profile.name
            amount_of_characters_to_query = random.randint(1, len(member_name))
            query = member_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_members = json.loads(response.content)
            response_members_count = len(response_members)
            if response_members_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_members_count, 1)
                retrieved_member = response_members[0]
                self.assertEqual(retrieved_member['id'], member.id)
            else:
                # Our community creator was retrieved too
                for response_member in response_members:
                    response_member_id = response_member['id']
                    self.assertTrue(
                        response_member_id == member.id or response_member_id == user.id)
            member.leave_community_with_name(community_name=community.name)

    def test_can_search_community_members_by_username(self):
        """
        should be able to search for community members by their username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        community = make_community(creator=user)

        amount_of_community_members_to_search_for = 5

        for i in range(0, amount_of_community_members_to_search_for):
            member = make_user()
            member.join_community_with_name(community_name=community.name)
            member_username = member.username
            amount_of_characters_to_query = random.randint(1, len(member_username))
            query = member_username[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url(community_name=community.name)
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_members = json.loads(response.content)
            response_members_count = len(response_members)
            if response_members_count == 1:
                # Our community creator was not retrieved
                self.assertEqual(response_members_count, 1)
                retrieved_member = response_members[0]
                self.assertEqual(retrieved_member['id'], member.id)
            else:
                # Our community creator was retrieved too
                for response_member in response_members:
                    response_member_id = response_member['id']
                    self.assertTrue(
                        response_member_id == member.id or response_member_id == user.id)

            member.leave_community_with_name(community_name=community.name)

    def test_can_filter_administrators_from_members_search(self):
        """
        should be able to filter the administrators from the search members of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        similar_username = fake.user_name()

        community_creator = make_user(username=similar_username + fake.word())
        community = make_community(creator=community_creator, type='P')
        community_name = community.name

        community_member = make_user(username=similar_username + fake.word())
        community_member.join_community_with_name(community_name=community_name)

        community_moderator = make_user(username=similar_username + fake.word())
        community_moderator.join_community_with_name(community_name=community_name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        community_administrator = make_user(username=similar_username + fake.word())
        community_administrator.join_community_with_name(community_name=community_name)
        community_creator.add_administrator_with_username_to_community_with_name(
            username=community_administrator.username,
            community_name=community.name)

        expected_members = [
            community_member,
            community_moderator,
            # Creator is administrator too
            # community_creator,
        ]

        expected_members_ids = [member.pk for member in expected_members]

        url = self._get_url(community_name=community.name)

        response = self.client.get(url, {
            'query': similar_username,
            'exclude': Community.EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD,
        }, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(expected_members))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, expected_members_ids)

    def test_can_filter_moderators_from_members_search(self):
        """
        should be able to filter the moderators from the search members of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        similar_username = fake.user_name()

        community_creator = make_user(username=similar_username + fake.word())
        community = make_community(creator=community_creator, type='P')
        community_name = community.name

        community_member = make_user(username=similar_username + fake.word())
        community_member.join_community_with_name(community_name=community_name)

        community_moderator = make_user(username=similar_username + fake.word())
        community_moderator.join_community_with_name(community_name=community_name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        community_administrator = make_user(username=similar_username + fake.word())
        community_administrator.join_community_with_name(community_name=community_name)
        community_creator.add_administrator_with_username_to_community_with_name(
            username=community_administrator.username,
            community_name=community.name)

        expected_members = [
            community_member,
            community_administrator,
            community_creator,
        ]

        expected_members_ids = [member.pk for member in expected_members]

        url = self._get_url(community_name=community.name)

        response = self.client.get(url, {
            'query': similar_username,
            'exclude': Community.EXCLUDE_COMMUNITY_MODERATORS_KEYWORD,
        }, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(expected_members))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, expected_members_ids)

    def test_can_filter_moderators_and_administrators_from_members_search(self):
        """
        should be able to filter the moderators and administrators from the search members of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        community_member = make_user()
        community_member.join_community_with_name(community_name=community_name)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community_name)
        other_user.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                      community_name=community.name)

        community_administrator = make_user()
        community_administrator.join_community_with_name(community_name=community_name)
        other_user.add_administrator_with_username_to_community_with_name(username=community_administrator.username,
                                                                          community_name=community.name)

        expected_members = [
            community_member
        ]

        expected_members_ids = [member.pk for member in expected_members]

        url = self._get_url(community_name=community.name)

        response = self.client.get(url, {
            'query': community_member.username,
            'exclude': ','.join(
                [Community.EXCLUDE_COMMUNITY_MODERATORS_KEYWORD, Community.EXCLUDE_COMMUNITY_ADMINISTRATORS_KEYWORD]),
        }, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_members = json.loads(response.content)

        self.assertEqual(len(response_members), len(expected_members))

        for response_member in response_members:
            response_member_id = response_member.get('id')
            self.assertIn(response_member_id, expected_members_ids)

    def _get_url(self, community_name):
        return reverse('search-community-members', kwargs={
            'community_name': community_name,
        })


class LeaveCommunityAPITests(OpenbookAPITestCase):

    def test_leaving_community_should_remove_notifications_subscription(self):
        """
        when leaving a community, the member community notifications subscription should be removed
        """
        user = make_user()
        other_user = make_user()

        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=other_user)
        community_name = community.name

        user.join_community_with_name(community_name=community_name)

        user.enable_new_post_notifications_for_community_with_name(community_name=community_name)

        url = self._get_url(community_name=community_name)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            CommunityNotificationsSubscription.objects.filter(subscriber=user, community=community).exists())

    def _get_url(self, community_name):
        return reverse('community-leave', kwargs={
            'community_name': community_name,
        })
