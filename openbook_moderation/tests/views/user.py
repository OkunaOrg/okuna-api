import json

from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_common.tests.helpers import make_global_moderator, make_user, make_moderation_category, \
    make_authentication_headers_for_user, make_moderation_penalty
from openbook_moderation.models import ModeratedObject, \
    ModerationCategory, ModerationPenalty

fake = Faker()


class UserModerationPenaltiesAPITests(APITestCase):
    """
    UserModerationPenaltiesAPI
    """

    def test_can_retrieve_own_moderation_penalties(self):
        """
        should be able to retrieve own moderation penalties
        :return:
        """

        user = make_user()

        amount_of_moderation_penalties = 5
        moderation_penalties_ids = []

        for i in range(0, amount_of_moderation_penalties):
            moderation_penalty = make_moderation_penalty(user=user)
            moderation_penalties_ids.append(moderation_penalty.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderation_penalties = json.loads(response.content)

        self.assertEqual(len(response_moderation_penalties), len(moderation_penalties_ids))

        for response_moderationCategory in response_moderation_penalties:
            response_moderation_category_id = response_moderationCategory.get('id')
            self.assertIn(response_moderation_category_id, moderation_penalties_ids)

    def test_cant_retrieve_other_user_moderation_penalties(self):
        """
        should not be able to retrieve other user moderation penalties
        :return:
        """

        other_user = make_user()
        user = make_user()

        amount_of_moderation_penalties = 5
        moderation_penalties_ids = []

        for i in range(0, amount_of_moderation_penalties):
            moderation_penalty = make_moderation_penalty(user=user)
            moderation_penalties_ids.append(moderation_penalty.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(other_user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderation_penalties = json.loads(response.content)

        self.assertEqual(len(response_moderation_penalties), 0)

    def _get_url(self):
        return reverse('user-moderation-penalties')
