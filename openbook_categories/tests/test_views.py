import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_category

fake = Faker()


class CategoriesAPITests(OpenbookAPITestCase):
    """
    CategoriesAPI
    """

    def test_can_retrieve_categories(self):
        """
        should be able to retrieve all categories and return 200
        """
        user = make_user()

        amount_of_categories = 5
        categories_ids = []

        for i in range(0, amount_of_categories):
            category = make_category()
            categories_ids.append(category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_categories = json.loads(response.content)

        self.assertEqual(len(response_categories), len(categories_ids))

        for response_category in response_categories:
            response_category_id = response_category.get('id')
            self.assertIn(response_category_id, categories_ids)

    def _get_url(self):
        return reverse('categories')
