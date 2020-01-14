import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_moderation_category, \
    make_authentication_headers_for_user, make_moderation_penalty, make_community, make_fake_post_text

fake = Faker()


class UserModerationPenaltiesAPITests(OpenbookAPITestCase):
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


class UserPendingModeratedObjectsCommunitiesAPITests(OpenbookAPITestCase):
    """
    UserPendingModeratedObjectsCommunitiesAPI
    """

    def test_can_retrieve_pending_moderated_objects_communities_of_moderated_communities(self):
        """
        should be able to retrieve pending moderated objects communities of moderated communities
        :return:
        """

        user = make_user()

        amount_of_pending_moderated_objects = 5

        amount_of_moderated_communities = 5
        moderated_commmunities_ids = []

        post_reporter = make_user()

        for i in range(0, amount_of_moderated_communities):
            community_creator = make_user()
            community = make_community(creator=community_creator)
            user.join_community_with_name(community_name=community.name)
            community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                                 username=user.username)

            for j in range(0, amount_of_pending_moderated_objects):
                post_creator = make_user()
                post_creator.join_community_with_name(community_name=community.name)
                post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
                post_reporter.report_post(post=post, category_id=make_moderation_category().pk)

            moderated_commmunities_ids.append(community.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(moderated_commmunities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            response_community_pending_moderated_objects_count = response_community.get(
                'pending_moderated_objects_count')
            self.assertIn(response_community_id, moderated_commmunities_ids)
            self.assertEqual(amount_of_pending_moderated_objects, response_community_pending_moderated_objects_count)

    def test_cant_retrieve_pending_moderated_objects_communities_of_moderated_communities(self):
        """
        should not be able to retrieve pending moderated objects communities of non moderated communities
        :return:
        """

        user = make_user()

        amount_of_pending_moderated_objects = 5

        amount_of_moderated_communities = 5

        post_reporter = make_user()

        for i in range(0, amount_of_moderated_communities):
            community_creator = make_user()
            community = make_community(creator=community_creator)
            user.join_community_with_name(community_name=community.name)

            for j in range(0, amount_of_pending_moderated_objects):
                post_creator = make_user()
                post_creator.join_community_with_name(community_name=community.name)
                post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
                post_reporter.report_post(post=post, category_id=make_moderation_category().pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(0, len(response_communities))

    def test_can_retrieve_pending_moderated_objects_communities_of_administrated_communities(self):
        """
        should be able to retrieve pending moderated objects communities of administrated communities
        :return:
        """

        user = make_user()

        amount_of_pending_moderated_objects = 5

        amount_of_administrated_communities = 5
        moderated_commmunities_ids = []

        post_reporter = make_user()

        for i in range(0, amount_of_administrated_communities):
            community_creator = make_user()
            community = make_community(creator=community_creator)
            user.join_community_with_name(community_name=community.name)
            community_creator.add_administrator_with_username_to_community_with_name(community_name=community.name,
                                                                                     username=user.username)

            for j in range(0, amount_of_pending_moderated_objects):
                post_creator = make_user()
                post_creator.join_community_with_name(community_name=community.name)
                post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
                post_reporter.report_post(post=post, category_id=make_moderation_category().pk)

            moderated_commmunities_ids.append(community.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(moderated_commmunities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            response_community_pending_moderated_objects_count = response_community.get(
                'pending_moderated_objects_count')
            self.assertIn(response_community_id, moderated_commmunities_ids)
            self.assertEqual(amount_of_pending_moderated_objects, response_community_pending_moderated_objects_count)

    def test_cant_retrieve_pending_moderated_objects_communities_of_administrated_communities(self):
        """
        should not be able to retrieve pending moderated objects communities of non administrated communities
        :return:
        """

        user = make_user()

        amount_of_pending_moderated_objects = 5

        amount_of_administrated_communities = 5

        post_reporter = make_user()

        for i in range(0, amount_of_administrated_communities):
            community_creator = make_user()
            community = make_community(creator=community_creator)
            user.join_community_with_name(community_name=community.name)

            for j in range(0, amount_of_pending_moderated_objects):
                post_creator = make_user()
                post_creator.join_community_with_name(community_name=community.name)
                post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
                post_reporter.report_post(post=post, category_id=make_moderation_category().pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(0, len(response_communities))

    def _get_url(self):
        return reverse('user-pending-moderated-objects-communities')
