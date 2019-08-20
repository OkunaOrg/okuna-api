from django.urls import reverse
from faker import Faker
from rest_framework.test import APITestCase
from rest_framework import status

import logging
import json

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community, make_fake_post_text, make_post_image, make_moderation_category
from openbook_communities.models import Community
from openbook_moderation.models import ModeratedObject
from openbook_posts.models import Post, PostUserMention

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

    def test_cannot_retrieve_soft_deleted_posts_from_community(self):
        """
        should not be able to retrieve soft deleted posts of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        amount_of_community_posts = 5

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_member_post.soft_delete()

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cannot_retrieve_moderated_approved_posts_from_community(self):
        """
        should not be able to retrieve moderated approved posts of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        community_name = community.name
        post_reporter = make_user()

        amount_of_community_posts = 5

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            moderation_category = make_moderation_category()
            post_reporter.report_post(post=community_member_post, category_id=moderation_category.pk)

            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=community_member_post,
                                                                                       category_id=moderation_category.pk)

            community_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cannot_retrieve_reported_posts_from_community(self):
        """
        should not be able to retrieve reported posts of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)
        user.join_community_with_name(community_name=community.name)

        community_name = community.name

        amount_of_community_posts = 5

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            moderation_category = make_moderation_category()
            user.report_post(post=community_member_post, category_id=moderation_category.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_can_retrieve_moderated_rejected_posts_from_community(self):
        """
        should be able to retrieve moderated rejected posts of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        community_name = community.name
        post_reporter = make_user()
        community_posts_ids = []

        amount_of_community_posts = 5

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_posts_ids.append(community_member_post.pk)
            moderation_category = make_moderation_category()
            post_reporter.report_post(post=community_member_post, category_id=moderation_category.pk)

            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=community_member_post,
                                                                                       category_id=moderation_category.pk)

            community_moderator.reject_moderated_object(moderated_object=moderated_object)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

    def test_can_retrieve_moderated_pending_posts_from_community(self):
        """
        should be able to retrieve moderated pending posts of a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')

        community_name = community.name
        post_reporter = make_user()

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_member = make_user()
            community_member.join_community_with_name(community_name=community_name)
            community_member_post = community_member.create_community_post(community_name=community.name,
                                                                           text=make_fake_post_text())
            community_posts_ids.append(community_member_post.pk)
            moderation_category = make_moderation_category()
            post_reporter.report_post(post=community_member_post, category_id=moderation_category.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(community_posts_ids))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, community_posts_ids)

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

    def test_cannot_retrieve_posts_from_blocked_user(self):
        """
        should not be able to retrieve the community posts for a blocked user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        user_to_block.create_community_post(community_name=community.name,
                                            text=make_fake_post_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_cannot_retrieve_posts_from_blocking_user(self):
        """
        should not be able to retrieve the community posts for a blocking user and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        user_to_block.create_community_post(community_name=community.name,
                                            text=make_fake_post_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_can_retrieve_posts_from_blocked_staff_member(self):
        """
        should be able to retrieve the community posts for a blocked staff member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name,
                                                     text=make_fake_post_text())

        user.block_user_with_id(user_id=community_owner.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        response_post_id = response_post.get('id')
        self.assertEqual(response_post_id, post.pk)

    def test_can_retrieve_posts_from_blocking_staff_member(self):
        """
        should be able to retrieve the community posts for a blocking staff member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name,
                                                     text=make_fake_post_text())

        community_owner.block_user_with_id(user_id=user.pk)

        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        response_post_id = response_post.get('id')
        self.assertEqual(response_post_id, post.pk)

    def test_can_retrieve_posts_from_blocking_member_if_staff(self):
        """
        should be able to retrieve the community posts of a blocking member if staff and return 200
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community_name=community.name,
                                          text=make_fake_post_text())

        user.block_user_with_id(user_id=community_owner.pk)

        headers = make_authentication_headers_for_user(community_owner)
        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        response_post_id = response_post.get('id')
        self.assertEqual(response_post_id, post.pk)

    def test_can_retrieve_posts_from_blocked_member_if_staff(self):
        """
        should be able to retrieve the community posts of a blocked member if staff and return 200
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community_name=community.name,
                                          text=make_fake_post_text())

        community_owner.block_user_with_id(user_id=user.pk)

        headers = make_authentication_headers_for_user(community_owner)
        url = self._get_url(community_name=community.name)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        response_post_id = response_post.get('id')
        self.assertEqual(response_post_id, post.pk)

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

    def test_can_create_community_post_draft(self):
        """
        should be able to create an post draft for a community part of and return 201
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(creator=community_creator, type='P')

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(community_name=community.name)

        post_text = make_fake_post_text()

        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, {
            'text': post_text,
            'is_draft': True
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user.posts.filter(text=post_text, status=Post.STATUS_DRAFT).count(), 1)

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

    def test_create_public_community_post_detects_mention(self):
        """
        should detect mentions when creating a public community post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        community = make_community()

        mentioned_user = make_user()
        user.join_community_with_name(community_name=community.name)

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
        }

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertTrue(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_private_community_post_does_not_detects_mention_if_not_part_of(self):
        """
        should not detect mentions when creating a private community post not part of
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        community_owner = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_owner)

        mentioned_user = make_user()
        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
        }

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertFalse(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_private_community_post_detects_mention_if_part_of(self):
        """
        should detect mentions when creating a private community post part of
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        community_owner = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_owner)

        mentioned_user = make_user()

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=mentioned_user.username,
                                                                         community_name=community.name)
        mentioned_user.join_community_with_name(community_name=community.name)

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
        }

        url = self._get_url(community_name=community.name)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertTrue(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

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
