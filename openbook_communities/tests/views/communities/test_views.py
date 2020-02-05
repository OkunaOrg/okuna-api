# Create your tests here.
import random

from django.urls import reverse
from django.conf import settings
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community_avatar, make_community_cover, make_category, make_community_users_adjective, \
    make_community_user_adjective, make_community
from openbook_common.utils.model_loaders import get_community_model
from openbook_communities.models import Community

logger = logging.getLogger(__name__)
fake = Faker()


class CommunitiesAPITests(OpenbookAPITestCase):
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

    def test_cannot_create_community_without_credentials(self):
        """
        should NOT be able to create a community without providing credentials and return 400
        """

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
            'categories': community_categories,
        }

        url = self._get_url()

        response = self.client.put(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(
            Community.objects.filter(name=community_name, title=community_title, color=community_color,
                                     type=community_type).count() == 1)

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
            'categories': community_categories,
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

    def test_create_community_should_make_creator_admin(self):
        """
        should make the community creator an administrator when creating a new community
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
            'categories': community_categories,
        }

        url = self._get_url()

        self.client.put(url, data, **headers, format='multipart')

        self.assertTrue(user.is_administrator_of_community_with_name(community_name=community_name))

    def test_create_community_should_not_make_creator_mod(self):
        """
        should NOT make the community creator a moderator when creating a new community
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
            'categories': community_categories,
        }

        url = self._get_url()

        self.client.put(url, data, **headers, format='multipart')

        self.assertFalse(user.is_moderator_of_community_with_name(community_name=community_name))

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
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Community.objects.filter(name=community_name, title=community_title, description=community_description,
                                     rules=community_rules,
                                     color=community_color,
                                     type=community_type).count() == 1)

    def test_create_private_community_should_disable_member_invites(self):
        """
        should be able to create a private community and automatically disable member invites and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_color = fake.hex_color()
        community_categories = []
        community_type = Community.COMMUNITY_TYPE_PRIVATE

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Community.objects.filter(name=community_name, title=community_title, description=community_description,
                                     rules=community_rules, color=community_color,
                                     type=community_type, invites_enabled=False).count() == 1)

    def test_create_public_community_should_enable_member_invites(self):
        """
        should be able to create a public community and automatically emnable member invites and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        community_title = fake.name_male()
        community_description = fake.text(max_nb_chars=settings.COMMUNITY_DESCRIPTION_MAX_LENGTH)
        community_rules = fake.text(max_nb_chars=settings.COMMUNITY_RULES_MAX_LENGTH)
        community_color = fake.hex_color()
        community_categories = []
        community_type = Community.COMMUNITY_TYPE_PUBLIC

        for i in range(0, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            community_categories.append(category.name)

        data = {
            'name': community_name,
            'type': community_type,
            'title': community_title,
            'description': community_description,
            'rules': community_rules,
            'color': community_color,
            'categories': community_categories
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        community = Community.objects.get(name=community_name)

        self.assertTrue(community.invites_enabled)

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
        community_user_adjective = make_community_user_adjective()
        community_users_adjective = make_community_users_adjective()
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

    def _get_url(self):
        return reverse('communities')


class JoinedCommunities(OpenbookAPITestCase):
    def test_retrieve_joined_communities(self):
        """
        should be able to retrieve all own communities return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]
        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_retrieve_joined_communities_offset(self):
        """
        should be able to retrieve all own communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        community_creator = make_user()
        communities = []

        for i in range(0, total_amount_of_communities):
            community = make_community(creator=community_creator)
            communities.append(community)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def test_can_retrieve_only_joined_communities_not_excluded_from_profile_posts(self):
        """
        should be able to retrieve for only joined communities not excluded from profile posts and return 200
        """
        user = make_user()

        non_excluded_community_owner = make_user()
        non_excluded_community = make_community(creator=non_excluded_community_owner, name='memes')

        excluded_community_owner = make_user()
        excluded_community = make_community(creator=excluded_community_owner, name='memestwo')

        user.join_community_with_name(community_name=non_excluded_community.name)
        user.join_community_with_name(community_name=excluded_community.name)

        user.exclude_community_from_profile_posts(community=excluded_community)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'excluded_from_profile_posts': False
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parsed_response = json.loads(response.content)
        self.assertEqual(len(parsed_response), 1)

        retrieved_community = parsed_response[0]

        self.assertEqual(retrieved_community['name'], non_excluded_community.name)

    def _get_url(self):
        return reverse('joined-communities')


class SearchJoinedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchJoinedCommunitiesAPI
    """

    def test_can_search_joined_communities_by_name(self):
        """
        should be able to search for joined communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.join_community_with_name(community_name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_joined_communities_by_title(self):
        """
        should be able to search for joined communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = mixer.blend(Community, title=community_title, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.join_community_with_name(community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def test_can_search_only_joined_communities_not_excluded_from_profile_posts(self):
        """
        should be able to search for only joined communities not excluded from profile posts and return 200
        """
        user = make_user()

        non_excluded_community_owner = make_user()
        non_excluded_community = make_community(creator=non_excluded_community_owner, name='memes')

        excluded_community_owner = make_user()
        excluded_community = make_community(creator=excluded_community_owner, name='memestwo')

        user.join_community_with_name(community_name=non_excluded_community.name)
        user.join_community_with_name(community_name=excluded_community.name)

        user.exclude_community_from_profile_posts(community=excluded_community)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'query': 'memes',
            'excluded_from_profile_posts': False
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parsed_response = json.loads(response.content)
        self.assertEqual(len(parsed_response), 1)

        retrieved_community = parsed_response[0]

        self.assertEqual(retrieved_community['name'], non_excluded_community.name)

    def _get_url(self):
        return reverse('search-joined-communities')


class AdministratedCommunities(OpenbookAPITestCase):
    def test_retrieve_administrated_communities(self):
        """
        should be able to retrieve all administrated communities return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_communities = 5
        communities_ids = []

        for i in range(0, amount_of_communities):
            community = make_community(creator=user)
            communities_ids.append(community.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_retrieve_administrated_communities_offset(self):
        """
        should be able to retrieve all own communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        communities = []
        community_creator = make_user()

        for i in range(0, total_amount_of_communities):
            community = make_community(creator=community_creator)
            communities.append(community)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                     community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def _get_url(self):
        return reverse('administrated-communities')


class SearchAdministratedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchAdministratedCommunitiesAPI
    """

    def test_can_search_administrated_communities_by_name(self):
        """
        should be able to search for administrated communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_administrated_communities_to_search_for = 5

        for i in range(0, amount_of_administrated_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = make_community(creator=user, name=community_name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_administrated_communities_by_title(self):
        """
        should be able to search for administrated communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_administrated_communities_to_search_for = 5

        for i in range(0, amount_of_administrated_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = make_community(creator=user, title=community_title)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('search-administrated-communities')


class ModeratedCommunities(OpenbookAPITestCase):
    def test_retrieve_moderated_communities(self):
        """
        should be able to retrieve all moderated communities return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_communities = 5
        communities_ids = []

        for i in range(0, amount_of_communities):
            other_user = make_user()
            community = make_community(creator=other_user)
            user.join_community_with_name(community_name=community.name)
            other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                          community_name=community.name)
            communities_ids.append(community.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_retrieve_moderated_communities_offset(self):
        """
        should be able to retrieve all moderated communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        community_creator = make_user()
        communities = []

        for i in range(0, total_amount_of_communities):
            community = make_community(creator=community_creator)
            communities.append(community)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def _get_url(self):
        return reverse('moderated-communities')


class SearchModeratedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchModeratedCommunitiesAPITests
    """

    def test_can_search_moderated_communities_by_name(self):
        """
        should be able to search for moderated communities by their name and return 200
        """
        user = make_user()
        community_creator = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_moderated_communities_to_search_for = 5

        for i in range(0, amount_of_moderated_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = make_community(creator=community_creator, name=community_name)
            user.join_community_with_name(community_name=community.name)
            community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_moderated_communities_by_title(self):
        """
        should be able to search for moderated communities by their title and return 200
        """
        user = make_user()
        community_creator = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_moderated_communities_to_search_for = 5

        for i in range(0, amount_of_moderated_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = make_community(creator=community_creator, title=community_title)
            user.join_community_with_name(community_name=community.name)
            community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('search-moderated-communities')


class FavoriteCommunities(OpenbookAPITestCase):
    def test_retrieve_favorite_communities(self):
        """
        should be able to retrieve all favorite communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]
        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.favorite_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_should_not_retrieve_non_favorite_communities(self):
        """
        should NOT retrieve non-favorite communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), 0)

    def test_retrieve_favorite_communities_offset(self):
        """
        should be able to retrieve all favorite communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        communities = mixer.cycle(total_amount_of_communities).blend(Community, creator=user)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.favorite_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def _get_url(self):
        return reverse('favorite-communities')


class SearchFavoriteCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchFavoriteCommunitiesAPI
    """

    def test_can_search_favorite_communities_by_name(self):
        """
        should be able to search for favorite communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_subscribed_communities_to_search_for = 5

        for i in range(0, amount_of_subscribed_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.join_community_with_name(community_name)
            user.favorite_community_with_name(community_name=community.name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_favorite_communities_by_title(self):
        """
        should be able to search for favorite communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_subscribed_communities_to_search_for = 5

        for i in range(0, amount_of_subscribed_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = mixer.blend(Community, title=community_title, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.join_community_with_name(community.name)
            user.favorite_community_with_name(community_name=community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('search-favorite-communities')


class CommunityNameCheckAPITests(OpenbookAPITestCase):
    """
    CommunityNameCheckAPI
    """

    def test_communityName_not_taken(self):
        """
        should return status 202 if community name is not taken.
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        request_data = self._get_request_data(community_name)

        url = self._get_url()
        response = self.client.post(url, request_data, **headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_community_name_taken(self):
        """
        should return status 400 if the communityName is taken
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_name = fake.user_name()
        request_data = self._get_request_data(community_name)
        community = mixer.blend(Community, name=community_name)

        url = self._get_url()
        response = self.client.post(url, request_data, **headers, format='json')

        parsed_response = json.loads(response.content)

        self.assertIn('name', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_community_name(self):
        """
        should return 400 if the communityName is not a valid one
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        community_names = ('lifenau!', 'p-o-t-a-t-o', '.a!', 'dexter@', '🤷‍♂️', 'hola ahi')

        for community_name in community_names:
            request_data = self._get_request_data(community_name)
            response = self.client.post(url, request_data, **headers, format='json')
            parsed_response = json.loads(response.content)
            self.assertIn('name', parsed_response)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_community_name(self):
        """
        should return 202 if the communityName is a valid name
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        url = self._get_url()
        community_names = ('lifenautjoe', 'shantanu_123', 'm4k3l0v3n0tw4r', 'o_0')
        for community_name in community_names:
            request_data = self._get_request_data(community_name)
            response = self.client.post(url, request_data, **headers, format='json')
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def _get_request_data(self, name):
        return {'name': name}

    def _get_url(self):
        return reverse('community-name-check')


class SearchCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchCommunitiesAPITests
    """

    def test_can_search_communities_by_name(self):
        """
        should be able to search for communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_communities_to_search_for = 5

        for i in range(0, amount_of_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name)
            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]
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
            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_communities_by_title(self):
        """
        should be able to search for communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_communities_to_search_for = 5

        for i in range(0, amount_of_communities_to_search_for):
            community = mixer.blend(Community)
            community_title = community.title
            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]
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
            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title)
            community.delete()

    def test_can_search_communities_banned_from(self):
        """
        should be able to search for communities banned from and return 200
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)
        community_title = community.title

        user.join_community_with_name(community_name=community.name)

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'query': community_title
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parsed_response = json.loads(response.content)
        self.assertEqual(len(parsed_response), 1)

        retrieved_community = parsed_response[0]
        self.assertEqual(retrieved_community['name'], community.name)

    def test_can_search_only_communities_not_excluded_from_profile_posts(self):
        """
        should be able to search for only communities not excluded from profile posts and return 200
        """
        user = make_user()

        non_excluded_community_owner = make_user()
        non_excluded_community = make_community(creator=non_excluded_community_owner, name='memes')

        excluded_community_owner = make_user()
        excluded_community = make_community(creator=excluded_community_owner, name='memestwo')

        user.exclude_community_from_profile_posts(community=excluded_community)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'query': 'memes',
            'excluded_from_profile_posts': False
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parsed_response = json.loads(response.content)
        self.assertEqual(len(parsed_response), 1)

        retrieved_community = parsed_response[0]

        self.assertEqual(retrieved_community['name'], non_excluded_community.name)

    def _get_url(self):
        return reverse('search-communities')


class TrendingCommunitiesAPITests(OpenbookAPITestCase):
    """
    TrendingCommunitiesAPITests
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_displays_public_communities(self):
        """
        should display public communities and return 200
        """
        user = make_user()

        amount_of_communities = 5
        communities_ids = []

        for i in range(0, amount_of_communities):
            community_owner = make_user()
            community = make_community(creator=community_owner)
            communities_ids.append(community.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_not_displays_private_communities(self):
        """
        should not display private communities and return 200
        """
        user = make_user()

        amount_of_communities = 5

        Community = get_community_model()

        for i in range(0, amount_of_communities):
            community_owner = make_user()
            community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), 0)

    def test_does_not_display_community_banned_from(self):
        """
        should not display a community banned from and return 200
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(0, len(response_communities))

    def _get_url(self):
        return reverse('trending-communities')


class TopPostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    TopPostsExcludedCommunitiesAPI
    """

    def test_retrieve_excluded_communities(self):
        """
        should be able to retrieve all excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]
        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_top_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_should_not_retrieve_non_excluded_communities(self):
        """
        should NOT retrieve non-excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), 0)

    def test_retrieve_excluded_communities_offset(self):
        """
        should be able to retrieve all excluded communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        communities = mixer.cycle(total_amount_of_communities).blend(Community, creator=user)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_top_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def _get_url(self):
        return reverse('legacy-top-posts-excluded-communities')


class SearchTopPostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchTopPostsExcludedCommunitiesAPI
    """

    def test_can_search_excluded_communities_by_name(self):
        """
        should be able to search for excluded communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_top_posts(community_name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_excluded_communities_by_title(self):
        """
        should be able to search for excluded communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = mixer.blend(Community, title=community_title, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_top_posts(community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

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

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('legacy-search-top-posts-excluded-communities')


class SuggestedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SuggestedCommunitiesAPI Tests
    """

    def test_should_return_communities_with_correct_id(self):
        """
        should return communities with ids mentioned in the environment var
        default id in settings is 1
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        # create a community with id 1 in case none exists in test db
        community = make_community(creator=user)

        url = self._get_url()
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)
        retrieved_community = parsed_response[0]

        self.assertEqual(len(parsed_response), 1)
        self.assertEqual(retrieved_community['id'], 1)

    def _get_url(self):
        return reverse('suggested-communities')
