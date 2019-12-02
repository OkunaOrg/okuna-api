# Create your tests here.
from unittest import mock

from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from unittest.mock import patch

from faker import Faker

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user
from openbook_invitations.models import UserInvite

logger = logging.getLogger(__name__)

fake = Faker()


class UserInvitesAPITests(OpenbookAPITestCase):
    """
    UserInvitesAPI
    """

    def test_create_invite(self):
        """
        should be able to create an invite and return 201
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        nickname = fake.name()
        data = {
            'nickname': nickname
        }

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        parsed_response = json.loads(response.content)
        user.refresh_from_db()

        invite_id = parsed_response['id']

        self.assertEqual(user.invite_count, (original_invite_count - 1))
        self.assertTrue(UserInvite.objects.filter(invited_by=user, nickname=nickname).exists())
        invite = UserInvite.objects.get(invited_by=user, nickname=nickname)
        self.assertEqual(invite.id, invite_id)

    def test_cannot_create_invite_if_count_is_zero(self):
        """
        should not be able to create an invite if invite_count is 0
        """
        user = make_user()
        nickname = fake.name()
        data = {
            'nickname': nickname
        }

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UserInvite.objects.filter(invited_by=user, nickname=nickname).exists())

    def test_cannot_create_invite_without_nickname(self):
        """
        should not be able to create an invite if no nickname is provided
        """
        user = make_user(invite_count=5)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, {}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UserInvite.objects.filter(invited_by=user).exists())

    def test_get_invites(self):
        """
        should be able to get invites list for user
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        total_invites = 5
        invited_ids = []

        for i in range(total_invites):
            nickname = fake.name()
            invite = user.create_invite(nickname=nickname)
            invited_ids.append(invite.id)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_invites = json.loads(response.content)

        self.assertEqual(total_invites, len(response_invites))
        for response_invite in response_invites:
            response_invite_id = response_invite.get('id')
            self.assertIn(response_invite_id, invited_ids)
        user.refresh_from_db()
        self.assertEqual(user.invite_count, original_invite_count - total_invites)

    def test_get_invites_with_status_accepted(self):
        """
        get all invites with status accepted
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)

        for i in range(original_invite_count - 1):
            nickname = fake.name()
            user.create_invite(nickname=nickname)

        invite.created_user = make_user()
        invite.save()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'pending': False
        }, **headers)

        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == 1)
        invite.refresh_from_db()
        self.assertTrue(invite.pk == parsed_response[0]['id'])

    def test_get_invites_with_status_pending(self):
        """
        get all invites with status pending
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)
        pending_invited_ids = []

        for i in range(original_invite_count - 1):
            nickname = fake.name()
            pending_invite = user.create_invite(nickname=nickname)
            pending_invited_ids.append(pending_invite.id)

        invite.created_user = make_user()
        invite.save()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'pending': True
        }, **headers)

        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == 4)
        for invite in parsed_response:
            self.assertIn(invite['id'], pending_invited_ids)

    def test_get_invites_count_offset(self):
        """
        should be able to get invites list with count and offset for user
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        total_invites = 5
        offset = count = 2
        offset_invited_ids = []  # 1 2 3 4 5

        for i in range(total_invites):
            nickname = fake.name()
            invite = user.create_invite(nickname=nickname)
            if i <= offset:
                offset_invited_ids.append(invite.id)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'count': count,
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_invites = json.loads(response.content)

        self.assertEqual(len(response_invites), count)
        for response_invite in response_invites:
            response_invite_id = response_invite.get('id')
            self.assertIn(response_invite_id, offset_invited_ids)
        user.refresh_from_db()
        self.assertEqual(user.invite_count, original_invite_count - total_invites)

    def _get_url(self):
        return reverse('invites')


class UserInviteSearchAPITests(OpenbookAPITestCase):

    def test_get_search_invites(self):
        """
        should be able to get invites with search
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        total_invites = 5
        invites = []

        for i in range(total_invites):
            nickname = fake.name()
            invite = user.create_invite(nickname=nickname)
            invites.append(invite)

        search = invites[0].nickname
        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'query': search,
            'pending': True
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_invites = json.loads(response.content)

        self.assertTrue(len(response_invites) == 1)
        self.assertEqual(response_invites[0]['id'], invites[0].id)

    def _get_url(self):
        return reverse('search-invites')

class UserInviteItemAPITests(OpenbookAPITestCase):
    """
    UserInvitesItemAPI
    """

    def test_can_delete_invite(self):
        """
        should be able to delete invite
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)

        url = self._get_url(invite.pk)
        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.invite_count, original_invite_count)
        self.assertFalse(UserInvite.objects.filter(id=invite.pk).exists())

    def test_cannot_delete_invite_if_invite_is_accepted(self):
        """
        should not be able to delete if an invite already has been accepted
        """
        original_invite_count = 5
        user = make_user(invite_count=original_invite_count)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)

        invite.created_user = make_user()
        invite.save()

        url = self._get_url(invite.pk)
        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertEqual(user.invite_count, original_invite_count - 1)
        self.assertTrue(UserInvite.objects.filter(id=invite.pk).exists())

    def test_can_update_invite(self):
        """
        should be able to update invite
        """
        user = make_user(invite_count=5)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)

        url = self._get_url(invite.pk)
        headers = make_authentication_headers_for_user(user)
        new_nickname = fake.name()
        response = self.client.patch(url, {
            'nickname': new_nickname
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invite.refresh_from_db()
        self.assertEqual(invite.nickname, new_nickname)

    def _get_url(self, invite_id):
        return reverse('invite', kwargs={
            'invite_id': invite_id
        })


class MockEmailMultiAlternatives:

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, alternatives=None,
                 cc=None, reply_to=None):
        pass

    def attach_alternative(self, content, mimetype):
        pass

    def send(self):
        pass


class UserInviteItemEmailAPI(OpenbookAPITestCase):
    """
    UserInviteItemEmail API
    """
    def test_can_send_email_to_invitee(self):
        """
        should be able to send invite email to invitee
        """
        user = make_user(invite_count=5)
        nickname = fake.name()
        invite = user.create_invite(nickname=nickname)

        url = self._get_url(invite.pk)
        headers = make_authentication_headers_for_user(user)
        with patch('django.core.mail.EmailMultiAlternatives', return_value=MockEmailMultiAlternatives):
            response = self.client.post(url, {
                'email': fake.email()
            }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invite.refresh_from_db()
        self.assertTrue(invite.is_invite_email_sent)

    def _get_url(self, invite_id):
        return reverse('send-invite-email', kwargs={
            'invite_id': invite_id
        })
