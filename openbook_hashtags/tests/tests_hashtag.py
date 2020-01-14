import json

from django.urls import reverse
from faker import Faker
from rest_framework import status

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_hashtag, \
    make_fake_post_text, make_community, make_circle, make_moderation_category, make_global_moderator
from openbook_common.tests.models import OpenbookAPITestCase
from openbook_communities.models import Community
from openbook_moderation.models import ModeratedObject

fake = Faker()


class HashtagAPITests(OpenbookAPITestCase):
    """
    HashtagAPITests
    """

    def test_can_retrieve_hashtag(self):
        """
        should be able to retrieve a hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        hashtag = make_hashtag()
        hashtag_name = hashtag.name

        url = self._get_url(hashtag_name=hashtag_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('name', parsed_response)
        response_name = parsed_response['name']
        self.assertEqual(response_name, hashtag_name)

    def test_can_retrieve_foreign_user_reported_hashtag(self):
        """
        should be able to retrieve a foreign user reported hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        hashtag = make_hashtag()
        hashtag_name = hashtag.name

        reporter = make_user()
        report_category = make_moderation_category()
        reporter.report_hashtag_with_name(hashtag_name=hashtag_name, category_id=report_category.pk)

        url = self._get_url(hashtag_name=hashtag_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('name', parsed_response)
        response_name = parsed_response['name']
        self.assertEqual(response_name, hashtag_name)

    def test_cant_retrieve_reported_hashtag(self):
        """
        should not be able to retrieve a reported hashtag and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        hashtag = make_hashtag()
        hashtag_name = hashtag.name

        report_category = make_moderation_category()
        user.report_hashtag_with_name(hashtag_name=hashtag_name, category_id=report_category.pk)

        url = self._get_url(hashtag_name=hashtag_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_retrieve_reported_and_approved_hashtag(self):
        """
        should not be able to retrieve a reported and approved hashtag and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        hashtag = make_hashtag()
        hashtag_name = hashtag.name

        reporter = make_user()
        report_category = make_moderation_category()
        reporter.report_hashtag_with_name(hashtag_name=hashtag_name, category_id=report_category.pk)

        global_moderator = make_global_moderator()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_hashtag(hashtag=hashtag,
                                                                                      category_id=report_category.pk)
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(hashtag_name=hashtag_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_retrieve_hashtag_with_posts_count(self):
        """
        should be able to retrieve a hashtag with its posts count and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        hashtag = make_hashtag()
        hashtag_name = hashtag.name

        amount_of_posts = 3

        for i in range(0, amount_of_posts):
            user = make_user()
            post_text = '#%s' % hashtag_name
            user.create_public_post(text=post_text)

        url = self._get_url(hashtag_name=hashtag_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('posts_count', parsed_response)
        posts_count = parsed_response['posts_count']
        self.assertEqual(posts_count, amount_of_posts)

    def _get_url(self, hashtag_name):
        return reverse('hashtag', kwargs={
            'hashtag_name': hashtag_name
        })


class HashtagPostsAPITests(OpenbookAPITestCase):
    """
    HashtagPostsAPITests
    """

    def test_retrieves_public_community_post_with_hashtag(self):
        """
        should retrieve posts with a given hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_community_post(community_name=community.name, text=fake_post_text)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 1)

        retrieved_posts = parsed_response[0]
        self.assertEqual(retrieved_posts['text'], fake_post_text)

    def test_retrieves_world_circle_post_with_hashtag(self):
        """
        should retrieve world circle post with a given hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_public_post(text=fake_post_text)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 1)

        retrieved_posts = parsed_response[0]
        self.assertEqual(retrieved_posts['text'], fake_post_text)

    def test_does_not_retrieve_private_community_not_part_of_post_with_hashtag(self):
        """
        should not retrieve a private community not part of post with a givne hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_creator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(community_name=community.name,
                                                                           username=post_creator.username)
        post_creator.join_community_with_name(community_name=community.name)

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_community_post(community_name=community.name, text=fake_post_text)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_does_not_retrieve_private_community_part_of_post_with_hashtag(self):
        """
        should not retrieve a private community part of post with a givne hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_creator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(community_name=community.name,
                                                                           username=post_creator.username)
        post_creator.join_community_with_name(community_name=community.name)

        community_creator.invite_user_with_username_to_community_with_name(community_name=community.name,
                                                                           username=user.username)
        user.join_community_with_name(community_name=community.name)

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_community_post(community_name=community.name, text=fake_post_text)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_does_not_retrieve_encircled_post_with_hashtag(self):
        """
        should not retrieve an encircled post with a givne hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        circle = make_circle(creator=post_creator)

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_encircled_post(circles_ids=[circle.pk], text=fake_post_text)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_does_not_retrieve_post_from_blocked_person_with_hashtag(self):
        """
        should not retrieve a post from a blocked person with a given hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_public_post(text=fake_post_text)

        user.block_user_with_username(username=post_creator.username)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_does_not_retrieve_post_from_blocking_person_with_hashtag(self):
        """
        should not retrieve a post from a blocking person with a given hashtag and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        hashtag = make_hashtag()

        fake_post_text = make_fake_post_text() + ' and a little hashtag #%s' % hashtag.name
        post_creator.create_public_post(text=fake_post_text)

        post_creator.block_user_with_username(username=user.username)

        url = self._get_url(hashtag_name=hashtag.name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def _get_url(self, hashtag_name):
        return reverse('hashtag-posts', kwargs={
            'hashtag_name': hashtag_name
        })
