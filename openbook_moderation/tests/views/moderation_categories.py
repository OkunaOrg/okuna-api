import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_moderation_category

fake = Faker()


class ModerationCategoriesAPITests(OpenbookAPITestCase):
    """
    ModerationCategoriesAPI
    """

    def test_can_retrieve_moderation_categories(self):
        """
        should be able to retrieve all moderationCategories and return 200
        """
        user = make_user()

        amount_of_moderationCategories = 5
        moderation_categories_ids = []

        for i in range(0, amount_of_moderationCategories):
            moderationCategory = make_moderation_category()
            moderation_categories_ids.append(moderationCategory.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_moderation_categories = json.loads(response.content)

        self.assertEqual(len(response_moderation_categories), len(moderation_categories_ids))

        for response_moderationCategory in response_moderation_categories:
            response_moderation_category_id = response_moderationCategory.get('id')
            self.assertIn(response_moderation_category_id, moderation_categories_ids)

    def _get_url(self):
        return reverse('moderation-categories')
