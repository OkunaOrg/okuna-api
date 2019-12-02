# Create your tests here.
import random

from django.urls import reverse
from faker import Faker
from rest_framework import status

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_hashtag_name, \
    make_hashtag
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import json


logger = logging.getLogger(__name__)
fake = Faker()


class SearchHashtagsAPITests(OpenbookAPITestCase):
    """
    SearchHashtagsAPITests
    """

    def test_can_search_hashtags_by_name(self):
        """
        should be able to search for hashtags by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_hashtags_to_search_for = 5

        for i in range(0, amount_of_hashtags_to_search_for):
            hashtag_name = make_hashtag_name()
            hashtag = make_hashtag(name=hashtag_name)
            amount_of_characters_to_query = random.randint(1, len(hashtag_name))
            query = hashtag_name[0:amount_of_characters_to_query]
            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()
            response = self.client.get(url, {
                'query': final_query
            }, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            parsed_response = json.loads(response.content)
            self.assertEqual(len(parsed_response), 1)
            retrieved_hashtag = parsed_response[0]
            self.assertEqual(retrieved_hashtag['name'], hashtag_name.lower())
            hashtag.delete()

    def _get_url(self):
        return reverse('search-hashtags')
