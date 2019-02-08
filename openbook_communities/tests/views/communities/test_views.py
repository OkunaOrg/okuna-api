# Create your tests here.
import random
import tempfile

from PIL import Image
from django.urls import reverse
from django.conf import settings
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User

import logging
import json

from openbook_common.models import Emoji
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_emoji, \
    make_community_avatar, make_community_cover, make_category
from openbook_communities.models import Community

logger = logging.getLogger(__name__)
fake = Faker()


class CommunitiesAPITests(APITestCase):
    """
    CommunitiesAPI
    """

    def test_cant_create_community_without_mandatory_params(self):
        """
        should NOT be able to create a community without providing mandatory params and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        mandatory_params = [
            'name',
            'type',
            'title',
            'color',
            'categories'
        ]

        url = self._get_url()

        response = self.client.put(url, {}, **headers, format='multipart')
        parsed_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        for param in mandatory_params:
            self.assertIn(param, parsed_response)

        self.assertTrue(
            Community.objects.all().count() == 0)

    def test_can_create_community_without_optional_params(self):
        """
        should be able to create a community without providing the optional arguments and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'T'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Community.objects.filter(name=community_name, title=community_title, color=community_color,
                                     type=community_type).count() == 1)

    def test_can_create_community_with_categories(self):
        """
        should be able to create a community with categories and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'T'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        community = Community.objects.get(name=community_name)

        categories = community.categories.all()
        categories_names = [category.name for category in categories]

        self.assertEqual(len(categories_names), len(community_categories))

        for community_category in community_categories:
            self.assertIn(community_category, categories_names)

    def test_cannot_create_a_category_with_exceeding_categories(self):
        """
        should NOT be able to create a community with an exceeding category amount and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'T'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT + 1):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Community.objects.filter(name=community_name).exists())

    def test_cannot_create_a_category_with_less_than_minimal_categories(self):
        """
        should NOT be able to create a community with a less that minimal category amount and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'T'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MIN_AMOUNT - 1):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Community.objects.filter(name=community_name).exists())

    def test_create_private_community(self):
        """
        should be able to create a private community and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_user_adjective = fake.word()
        community_users_adjective = fake.word()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'T'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'user_adjective': community_user_adjective,
            'users_adjective': community_users_adjective,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Community.objects.filter(name=community_name, title=community_title, description=community_description,
                                     rules=community_rules, user_adjective=community_user_adjective,
                                     users_adjective=community_users_adjective, color=community_color,
                                     type=community_type).count() == 1)

    def test_create_public_community(self):
        """
        should be able to create a public community and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_user_adjective = fake.word()
        community_users_adjective = fake.word()
        community_color = fake.hex_color()
        community_categories = []
        community_type = 'P'

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'user_adjective': community_user_adjective,
            'users_adjective': community_users_adjective,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Community.objects.filter(name=community_name, title=community_title, description=community_description,
                                     rules=community_rules, user_adjective=community_user_adjective,
                                     users_adjective=community_users_adjective, color=community_color,
                                     type=community_type).count() == 1)

    def test_create_community_with_avatar(self):
        """
        should be able to create a community with an avatar and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_user_adjective = fake.word()
        community_users_adjective = fake.word()
        community_avatar = make_community_avatar()
        community_color = fake.hex_color()
        community_categories = []

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': 'P',
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'user_adjective': community_user_adjective,
            'users_adjective': community_users_adjective,
            'color': community_color,
            'categories': community_categories,
            'avatar': community_avatar
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        community = Community.objects.get(name=community_name)
        self.assertTrue(hasattr(community, 'avatar'))

    def test_create_community_with_cover(self):
        """
        should be able to create a community with a cover and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_user_adjective = fake.word()
        community_users_adjective = fake.word()
        community_cover = make_community_cover()
        community_color = fake.hex_color()
        community_categories = []

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': 'P',
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'user_adjective': community_user_adjective,
            'users_adjective': community_users_adjective,
            'color': community_color,
            'categories': community_categories,
            'cover': community_cover
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        community = Community.objects.get(name=community_name)
        self.assertTrue(hasattr(community, 'cover'))

    def retrieve_own_communities(self):
        """
        should be able to retrieve all own communities return 200
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key
        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def _get_url(self):
        return reverse('communities')
