from django.urls import reverse
from faker import Faker
from rest_framework.test import APITestCase
from rest_framework import status

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community, make_fake_post_text, make_post_image
from openbook_posts.models import Post

logger = logging.getLogger(__name__)
fake = Faker()


class CommunityPostsAPITest(APITestCase):
    def test_can_retrieve_posts_from_public_community(self):
        """
        should be able to retrieve the posts for a public community and 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_posts_ids.append(community_member_post.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

    def test_can_retrieve_posts_with_max_id_and_count(self):
        """
        should be able to retrieve community posts with a max id and count
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_posts = 10
        count = 5
        max_id = 6
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_posts_ids.append(community_member_post.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, {
            'count': count,
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(count, len(response_posts))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertTrue(response_post_id < max_id)

    def test_can_retrieve_posts_from_private_community_member_of(self):
        """
        should be able to retrieve the posts for a private community member of and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        other_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                    community_name=community_name)
        user.join_community_with_name(community_name)

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            other_user.invite_user_with_username_to_community_with_name(username=community_member.username,
                                                                        community_name=community_name)
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_posts_ids.append(community_member_post.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

    def test_cannot_retrieve_posts_from_private_community_not_part_of(self):
        """
        should not be able to retrieve the posts for a private community not part of and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')

        other_user.create_community_post(community_name=community.name,
                                         text=make_fake_post_text())

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_posts_from_community_banned_from(self):
        """
        should not be able to retrieve the posts for a community banned from and return 403
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        community_owner.create_community_post(community_name=community.name,
                                              text=make_fake_post_text())

        user.join_community_with_name(community_name=community.name)

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_create_community_text_post_part_of(self):
        """
        should be able to create a post for a community part of and return 201
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)

        post_text = make_fake_post_text()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, {
            'text': post_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(text=post_text).exists())

    def test_can_create_community_image_post_part_of(self):
        """
        should be able to create an image post for a community part of and return 201
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)

        post_image = make_post_image()

        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, {
            'image': post_image
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(image__isnull=False).exists())

    def test_cant_create_community_post_not_part_of(self):
        """
        should not be able to create a post for a community part of and return 400
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')

        url = self._get_url(community_name=community.name)

        post_text = make_fake_post_text()

        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, {
            'text': post_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Post.objects.filter(text=post_text).exists())

    def _get_url(self, community_name):
        return reverse('community-posts', kwargs={
            'community_name': community_name
        })


class CommunityClosedPostsAPITest(APITestCase):

    def test_can_retrieve_closed_posts_from_community_if_administrator(self):
        """
        should be able to retrieve closed posts for a community if administrator
        """

        admin = make_user()
        community = make_community(creator=admin, type='P')
        community_name = community.name

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_member_post.is_closed = True
            community_member_post.save()
            community_posts_ids.append(community_member_post.pk)

        headers = make_authentication_headers_for_user(admin)
        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

    def test_can_retrieve_closed_posts_from_community_if_moderator(self):
        """
        should be able to retrieve closed posts for a community if moderator
        """

        moderator = make_user()
        admin = make_user()
        community = make_community(creator=admin, type='P')

        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        community_name = community.name

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_member_post.is_closed = True
            community_member_post.save()
            community_posts_ids.append(community_member_post.pk)

        headers = make_authentication_headers_for_user(moderator)
        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

    def test_can_retrieve_closed_posts_with_max_id_and_count(self):
        """
        should be able to retrieve community closed posts with a max id and count if administrator/moderator
        """
        admin = make_user()
        community = make_community(creator=admin, type='P')
        community_name = community.name

        amount_of_community_posts = 10
        count = 5
        max_id = 6
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_member_post.is_closed = True
            community_member_post.save()
            community_posts_ids.append(community_member_post.pk)

        url = self._get_url(community_name=community.name)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.get(url, {
            'count': count,
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(count, len(response_posts))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertTrue(response_post_id < max_id)

    def test_cannot_retrieve_closed_posts_from_community_if_member(self):
        """
        should not be able to retrieve closed posts for a community if just a member
        """

        admin = make_user()
        community = make_community(creator=admin, type='P')

        community_name = community.name

        community_member = make_user()
        community_member.join_community_with_name(community_name=community_name)

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_member_post.is_closed = True
            community_member_post.save()
            community_posts_ids.append(community_member_post.pk)

        headers = make_authentication_headers_for_user(community_member)
        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, community_name):
        return reverse('closed-community-posts', kwargs={
            'community_name': community_name
        })
