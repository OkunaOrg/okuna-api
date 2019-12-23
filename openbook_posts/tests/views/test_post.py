# Create your tests here.
import json
import tempfile
from os import access, F_OK

from PIL import Image
from django.urls import reverse
from django_rq import get_worker
from django_rq.queues import get_queues
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from django.core.files.images import ImageFile
from django.core.files import File
from django.core.cache import cache
from django.conf import settings
from unittest import mock

import logging

from rq import SimpleWorker, Worker

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_moderation_category, \
    get_test_videos, get_test_image, make_proxy_blacklisted_domain, make_hashtag, make_hashtag_name, \
    make_reactions_emoji_group, make_emoji
from openbook_common.utils.model_loaders import get_language_model, get_community_new_post_notification_model, \
    get_post_comment_notification_model, get_post_comment_user_mention_notification_model, \
    get_post_user_mention_notification_model, get_post_comment_reaction_notification_model, \
    get_post_comment_reply_notification_model
from openbook_communities.models import Community
from openbook_hashtags.models import Hashtag
from openbook_notifications.models import PostUserMentionNotification, Notification
from openbook_posts.models import Post, PostUserMention, PostMedia
from openbook_common.models import ProxyBlacklistedDomain

logger = logging.getLogger(__name__)
fake = Faker()


def get_language_for_text_mock(text):
    return text


class PostItemAPITests(OpenbookAPITestCase):
    """
    PostItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_retrieve_own_post(self):
        """
        should be able to retrieve own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_foreign_user_public_post(self):
        """
        should be able to retrieve a foreign user public post and return 200
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_connected_user_encircled_post(self):
        """
        should be able to retrieve a connected user encircled post and return 200
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        user.connect_with_user_with_id(foreign_user.pk)
        foreign_user.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_public_community_not_member_of_post(self):
        """
        should be able to retrieve a public community not member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_public_community_member_of_post(self):
        """
        should be able to retrieve a public community member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_community_banned_from_post(self):
        """
        should not be able to retrieve a community banned from post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.join_community_with_name(community_name=community.name)
        user.comment_post(post, text=make_fake_post_comment_text())

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_private_community_not_member_of_post(self):
        """
        should not be able to retrieve a private community not member of post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_private_community_member_of_post(self):
        """
        should be able to retrieve a private community member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_user_encircled_post(self):
        """
        should not be able to retrieve a user encircled post and return 400
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_blocked_user_post(self):
        """
        should not be able to retrieve a post from a blocked user and return 400
        """
        user = make_user()
        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocking_user_post(self):
        """
        should not be able to retrieve a post from a blocking user and return 400
        """
        user = make_user()
        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocked_user_community_post(self):
        """
        should not be able to retrieve a community post from a blocked user and return 400
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocking_user_community_post(self):
        """
        should not be able to retrieve a community post from a blocking user and return 400
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user_to_block.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_can_retrieve_blocked_community_staff_post(self):
        """
        should be able to retrieve a the post of a blocked community staff member and return 200
        """
        user = make_user()
        community_owner = make_user()
        community = make_community(creator=community_owner)

        headers = make_authentication_headers_for_user(user)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.block_user_with_id(user_id=community_owner.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)
        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_blocking_community_staff_post(self):
        """
        should be able to retrieve a the post of a blocking community staff member and return 200
        """
        user = make_user()
        community_owner = make_user()
        community = make_community(creator=community_owner)

        headers = make_authentication_headers_for_user(user)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        community_owner.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)
        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_draft_own_post(self):
        """
        should be able to retrieve a draft own post
        """
        user = make_user()

        post = user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_can_retrieve_processing_own_post(self, mock):
        """
        should be able to retrieve an own processing post
        """
        user = make_user()

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_draft_foreign_user_post(self):
        """
        should not be able to retrieve a foreign user draft post
        """
        user = make_user()
        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_foreign_user_post(self, mock):
        """
        should not be able to retrieve a foreign user processing post
        """
        user = make_user()
        foreign_user = make_user()

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = foreign_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_draft_following_user_post(self):
        """
        should not be able to retrieve a following user draft post
        """
        user = make_user()
        following_user = make_user()

        user.follow_user(user=following_user)

        post = following_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_following_user_post(self, mock):
        """
        should not be able to retrieve a following user processing post
        """
        user = make_user()
        following_user = make_user()

        user.follow_user(user=following_user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = following_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_draft_follower_user_post(self):
        """
        should not be able to retrieve a follower user draft post
        """
        user = make_user()
        follower_user = make_user()

        follower_user.follow_user(user=user)

        post = follower_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_follower_user_post(self, mock):
        """
        should not be able to retrieve a follower user processing post
        """
        user = make_user()
        follower_user = make_user()

        follower_user.follow_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = follower_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_draft_connected_user_post(self):
        """
        should not be able to retrieve a follower user draft post
        """
        user = make_user()
        connected_user = make_user()

        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk)

        circle = make_circle(creator=connected_user)
        post = connected_user.create_encircled_post(text=make_fake_post_text(), is_draft=True, circles_ids=[circle.pk])

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_connected_user_post(self, mock):
        """
        should not be able to retrieve a follower user processing post
        """
        user = make_user()
        connected_user = make_user()

        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            circle = make_circle(creator=connected_user)
            post = connected_user.create_encircled_post(text=make_fake_post_text(), image=file, circles_ids=[circle.pk])

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_draft_pending_connection_user_post(self):
        """
        should not be able to retrieve a follower user draft post
        """
        user = make_user()
        pending_connection_user = make_user()

        user.connect_with_user_with_id(user_id=pending_connection_user.pk)

        circle = make_circle(creator=pending_connection_user)
        post = pending_connection_user.create_encircled_post(text=make_fake_post_text(), is_draft=True,
                                                             circles_ids=[circle.pk])

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_pending_connection_user_post(self, mock):
        """
        should not be able to retrieve a follower user processing post
        """
        user = make_user()
        pending_connection_user = make_user()

        user.connect_with_user_with_id(user_id=pending_connection_user.pk)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            circle = make_circle(creator=pending_connection_user)
            post = pending_connection_user.create_encircled_post(text=make_fake_post_text(), image=file,
                                                                 circles_ids=[circle.pk])

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_delete_own_post(self):
        """
        should be able to delete own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_delete_image_post(self):
        """
        should be able to delete image post and file
        """
        user = make_user()

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        image = ImageFile(tmp_file)

        post = user.create_public_post(text=make_fake_post_text(), image=image)
        file = post.image.image.file

        user.delete_post(post=post)

        self.assertFalse(access(file.name, F_OK))

    def test_delete_video_post(self):
        """
        should be able to delete video post and file
        """
        user = make_user()

        test_video = get_test_videos()[0]

        with open(test_video['path'], 'rb') as file:
            video = File(file)

            post = user.create_public_post(text=make_fake_post_text(), video=video)

            # Process videos
            get_worker('high', worker_class=SimpleWorker).work(burst=True)

            post_media_video = post.get_first_media()
            post_video = post_media_video.content_object

            video_files = [
                post_video.file.name
            ]

            for format in post_video.format_set.all():
                video_files.append(format.file.name)

            user.delete_post(post=post)

            for video_file in video_files:
                self.assertFalse(access(video_file, F_OK))

            self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_can_delete_post_of_community_if_mod(self):
        """
        should be able to delete a community post if moderator and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                             community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_can_delete_post_of_community_if_admin(self):
        """
        should be able to delete a community post if administrator and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_logs_community_post_deleted_by_non_creator(self):
        """
        should create a log when a community post was deleted by an admin/moderator
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertTrue(community.logs.filter(action_type='RP',
                                              source_user=user,
                                              target_user=community_post_creator).exists())

    def test_cannot_delete_foreign_post(self):
        """
        should not be able to delete a foreign post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 1)

    def test_can_edit_own_post(self):
        """
        should be able to edit own  post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.text, edited_text)
        self.assertTrue(post.is_edited)

    @mock.patch('openbook_posts.models.get_language_for_text')
    def test_editing_own_post_updates_language(self, get_language_for_text_call):
        """
        should update language when editing own  post and return 200
        """
        Language = get_language_model()
        get_language_for_text_call.return_value = Language.objects.get(pk=1)
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post.refresh_from_db()
        self.assertTrue(post.language is not None)

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }
        self.client.patch(url, data, **headers)
        get_language_for_text_call.assert_called_with(edited_text)

    def test_editing_own_post_updates_mentions(self):
        """
        should update mentions when updating text
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=post_text)

        post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk)

        newly_mentioned_user = make_user()

        post_text = 'Hello @' + newly_mentioned_user.username

        data = {
            'text': post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)
        new_post_user_mention = PostUserMention.objects.get(user_id=newly_mentioned_user.pk, post_id=post.pk)

        self.assertFalse(PostUserMention.objects.filter(user_id=mentioned_user.pk, post_id=post.pk).exists())
        self.assertEqual(PostUserMention.objects.filter(user_id=newly_mentioned_user.pk, post_id=post.pk).count(), 1)

        self.assertFalse(PostUserMentionNotification.objects.filter(post_user_mention_id=post_user_mention.pk,
                                                                    notification__owner_id=mentioned_user.pk,
                                                                    notification__notification_type=Notification.POST_USER_MENTION).exists())

        self.assertTrue(PostUserMentionNotification.objects.filter(post_user_mention_id=new_post_user_mention.pk,
                                                                   notification__owner_id=newly_mentioned_user.pk,
                                                                   notification__notification_type=Notification.POST_USER_MENTION).exists())

    def test_editing_text_post_ignores_non_existing_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames when editing a post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        fake_username = 'nonexistinguser'
        post_text = 'Hello @' + fake_username

        data = {
            'text': post_text
        }
        url = self._get_url(post=post)

        response = self.client.patch(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertEqual(PostUserMention.objects.filter(post_id=post.pk).count(), 0)

    def test_editing_text_post_ignores_casing_of_mentioned_usernames(self):
        """
        should ignores casing of mentioned usernames when editing a post
        """
        user = make_user()
        mentioned_user = make_user(username='Miguel')

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        cased_username = 'miguel'
        post_text = 'Hello @' + cased_username

        data = {
            'text': post_text
        }
        url = self._get_url(post=post)

        response = self.client.patch(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post = Post.objects.get(text=post_text, creator_id=user.pk)
        self.assertEqual(PostUserMention.objects.filter(user_id=mentioned_user.pk, post_id=post.pk).count(), 1)

    def test_editing_own_post_does_not_create_double_mentions(self):
        """
        should not create double mentions when editing our own post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=post_text)

        post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk)

        data = {
            'text': post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertEqual(PostUserMention.objects.filter(user_id=mentioned_user.pk, post_id=post.pk).count(), 1)
        new_post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk,
                                                            id=post_user_mention.pk)
        self.assertEqual(new_post_user_mention.pk, post_user_mention.pk)

    def test_editing_own_post_with_hashtag_creates_hashtag_if_not_exist(self):
        """
        when editing a post with a hashtag, should create  it if not exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag_name = make_hashtag_name()
        post_text = 'One hashtag #' + hashtag_name

        post = user.create_public_post(text=post_text)

        new_hashtag_name = make_hashtag_name()

        new_post_text = 'Another hashtag #' + new_hashtag_name

        data = {
            'text': new_post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=new_post_text, creator_id=user.pk)
        created_hashtag = Hashtag.objects.get(name=new_hashtag_name)
        self.assertTrue(post.hashtags.filter(pk=created_hashtag.pk).exists())
        self.assertEqual(post.hashtags.all().count(), 1)

    def test_editing_own_post_with_hashtag_updates_to_existing_hashtag_exists(self):
        """
        when editing a post with a hashtag, should update to it if exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()
        post_text = 'One hashtag #' + hashtag.name

        post = user.create_public_post(text=post_text)

        new_hashtag = make_hashtag()

        new_post_text = 'Another hashtag #' + new_hashtag.name

        data = {
            'text': new_post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=new_post_text, creator_id=user.pk)
        self.assertTrue(post.hashtags.filter(pk=new_hashtag.pk).exists())
        self.assertEqual(post.hashtags.all().count(), 1)

    def test_editing_own_post_with_hashtag_does_not_create_double_hashtags(self):
        """
        when editing a post with a hashtag, should not create duplicate hashtags
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()
        post_text = 'One hashtag #' + hashtag.name

        post = user.create_public_post(text=post_text)

        new_post_text = 'Same hashtag #' + hashtag.name

        data = {
            'text': new_post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=new_post_text, creator_id=user.pk)
        self.assertEqual(post.hashtags.filter(name=hashtag.name).count(), 1)
        self.assertEqual(post.hashtags.all().count(), 1)

    def test_edit_text_post_with_more_hashtags_than_allowed_should_not_edit_it(self):
        """
        when editing a post with more than allowed hashtags, should not create it
        """
        user = make_user()

        post_text = make_fake_post_text()

        post = user.create_public_post(text=post_text)

        headers = make_authentication_headers_for_user(user=user)
        post_hashtags = []

        for i in range(0, settings.POST_MAX_HASHTAGS + 1):
            hashtag = '#%s' % make_hashtag_name()
            post_hashtags.append(hashtag)

        new_post_text = ' '.join(post_hashtags)

        data = {
            'text': new_post_text
        }

        url = self._get_url(post=post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertTrue(Post.objects.filter(text=post_text).exists())

    def test_canot_edit_to_remove_text_from_own_text_only_post(self):
        """
        should not be able to edit to remove the text of an own post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        initial_text = make_fake_post_text()
        post = user.create_public_post(text=initial_text)

        url = self._get_url(post)
        data = {
            'text': ''
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertEqual(post.text, initial_text)
        self.assertFalse(post.is_edited)

    def test_can_edit_own_community_post(self):
        """
        should be able to edit own community post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(community_post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        community_post.refresh_from_db()
        self.assertEqual(community_post.text, edited_text)
        self.assertTrue(community_post.is_edited)

    def test_cannot_edit_own_community_post_which_is_closed(self):
        """
        should NOT be able to edit own closed community post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        original_text = make_fake_post_text()
        community_post = user.create_community_post(text=original_text, community_name=community.name)
        community_post.is_closed = True
        community_post.save()

        url = self._get_url(community_post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        community_post.refresh_from_db()
        self.assertEqual(community_post.text, original_text)
        self.assertFalse(community_post.is_edited)

    def test_cannot_edit_foreign_post(self):
        """
        should not be able to edit foreign post
        """
        user = make_user()
        foreign_user = make_user()
        headers = make_authentication_headers_for_user(user)
        original_text = make_fake_post_text()
        post = foreign_user.create_public_post(text=original_text)

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertEqual(post.text, original_text)
        self.assertFalse(post.is_edited)

    def test_cant_retrieve_soft_deleted_community_post(self):
        """
        should not be able to retrieve soft deleted community post
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post.soft_delete()

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_soft_deleted_following_user_post(self):
        """
        should not be able to retrieve soft deleted following user post
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        following_user_post.soft_delete()

        url = self._get_url(post=following_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_soft_deleted_connected_user_post(self):
        """
        should not be able to retrieve soft deleted connected user post
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user_post = connected_user.create_encircled_post(text=make_fake_post_text(),
                                                                   circles_ids=[connected_user_post_circle.pk])
        connected_user_post.soft_delete()
        connected_user_post.save()

        url = self._get_url(post=connected_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_community_post(self):
        """
        should not be able to retrieve reported community post
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        user.report_post(post=post, category_id=make_moderation_category().pk)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_following_user_post(self):
        """
        should not be able to retrieve reported following user post
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        user.report_post(post=following_user_post, category_id=make_moderation_category().pk)

        url = self._get_url(post=following_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_connected_user_post(self):
        """
        should not be able to retrieve reported connected user post
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user_post = connected_user.create_encircled_post(text=make_fake_post_text(),
                                                                   circles_ids=[connected_user_post_circle.pk])
        user.report_post(post=connected_user_post, category_id=make_moderation_category().pk)

        url = self._get_url(post=connected_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post):
        return reverse('post', kwargs={
            'post_uuid': post.uuid
        })


class MutePostAPITests(OpenbookAPITestCase):
    """
    MutePostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_mute_own_post(self):
        """
        should be able to mute own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cant_mute_own_post_if_already_muted(self):
        """
        should not be able to mute own post if already muted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        user.mute_post_with_id(post.pk)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_foreign_post_if_public_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cannot_mute_foreign_post_if_encircled_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_foreign_post_if_part_of_encircled_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        foreign_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=foreign_user.pk)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_community_post_if_public(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cannot_mute_closed_community_post(self):
        """
        should not be able to mute closed post if not admin/mod or post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_if_creator(self):
        """
        should be able to mute closed post if post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_administrator(self):
        """
        should be able to mute closed post if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(admin.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_if_moderator(self):
        """
        should be able to mute closed post if moderator in community
        """
        user = make_user()

        admin = make_user()
        moderator = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        headers = make_authentication_headers_for_user(moderator)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(moderator.has_muted_post_with_id(post.pk))

    def test_cant_mute_community_post_if_private_and_not_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_community_post_if_private_and_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        foreign_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def _get_url(self, post):
        return reverse('mute-post', kwargs={
            'post_uuid': post.uuid
        })


class UnmutePostAPITests(OpenbookAPITestCase):
    """
    UnmutePostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_unmute_own_post(self):
        """
        should be able to unmute own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        user.mute_post_with_id(post.pk)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_cant_unmute_own_post_if_already_unmuted(self):
        """
        should not be able to unmute own post if already unmuted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_cannot_unmute_closed_community_post(self):
        """
        should not be able to unmute closed post if not admin/mod or post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        user.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_if_creator(self):
        """
        should be able to unmute closed post if post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        user.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_administrator(self):
        """
        should be able to unmute closed post if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        admin.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(admin.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_if_moderator(self):
        """
        should be able to unmute closed post if moderator in community
        """
        user = make_user()

        admin = make_user()
        moderator = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        headers = make_authentication_headers_for_user(moderator)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        moderator.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(moderator.has_muted_post_with_id(post.pk))

    def _get_url(self, post):
        return reverse('unmute-post', kwargs={
            'post_uuid': post.uuid
        })


class PostCloseAPITests(OpenbookAPITestCase):
    """
    PostCloseAPITests APITests
    """

    def test_can_close_post_if_administrator_of_community(self):
        """
         should be able to close post if administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)
        self.assertTrue(parsed_response['is_closed'])

    def test_can_close_post_if_moderator_of_community(self):
        """
         should be able to close post if moderator of a community
        """
        user = make_user()
        admin = make_user()
        moderator = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)
        self.assertTrue(parsed_response['is_closed'])

    def test_cannot_close_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to close post if not moderator/administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)

    def test_logs_close_post_by_administrator_of_community(self):
        """
         should log close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='CP',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def test_close_post_deletes_new_post_notifications_for_normal_members(self):
        """
         should delete new post notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        community_member.enable_new_post_notifications_for_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        CommunityNewPostNotification = get_community_new_post_notification_model()
        self.assertFalse(CommunityNewPostNotification.objects.filter(notification__owner_id=community_member.pk,
                                                                     post_id=post.pk).exists())

    def test_close_post_deletes_post_user_mention_notifications_for_normal_members(self):
        """
         should delete post user mention notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        mentioned_user = make_user(username='joel123')
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        mentioned_user.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text='hey there @joel123')

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        PostUserMentionNotification = get_post_user_mention_notification_model()
        self.assertFalse(PostUserMentionNotification.objects.filter(
            notification__owner_id=mentioned_user.pk, post_user_mention__post=post).exists())

    def test_close_post_deletes_post_comment_notifications_for_normal_members(self):
        """
         should delete post comment notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        community_member_two = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        community_member_two.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())
        post_comment = community_member.comment_post(post=post, text=make_fake_post_text())
        post_comment_two = community_member_two.comment_post(post=post, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        PostCommentNotification = get_post_comment_notification_model()
        self.assertFalse(PostCommentNotification.objects.filter(notification__owner_id=community_member.pk,
                                                                post_comment=post_comment_two).exists())

    def test_close_post_deletes_post_comment_reaction_notifications_for_normal_members(self):
        """
         should delete post comment reaction notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        community_member_reactor = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        community_member_reactor.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())
        post_comment = community_member.comment_post(post=post, text=make_fake_post_text())

        # react
        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)
        community_post_comment_reply_reaction = community_member_reactor.react_to_post_comment(
            post_comment=post_comment,
            emoji_id=emoji.pk)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        PostCommentReactionNotification = get_post_comment_reaction_notification_model()
        self.assertFalse(PostCommentReactionNotification.objects.filter(
            notification__owner_id=community_member.pk,
            post_comment_reaction__post_comment=post_comment).exists())

    def test_close_post_deletes_post_comment_reply_notifications_for_normal_members(self):
        """
         should delete post comment reply notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        community_member_replier = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        community_member_replier.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())
        post_comment = community_member.comment_post(post=post, text=make_fake_post_text())
        post_comment_reply = community_member_replier.reply_to_comment_for_post(
            post_comment=post_comment,
            post=post,
            text=make_fake_post_comment_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        PostCommentReplyNotification = get_post_comment_reply_notification_model()
        self.assertFalse(PostCommentReplyNotification.objects.filter(
            notification__owner_id=community_member.pk,
            post_comment=post_comment_reply).exists())

    def test_close_post_deletes_post_comment_user_mention_notifications_for_normal_members(self):
        """
         should delete post comment user mention notifications for members (except creator/staff) on close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        mentioned_user = make_user(username='joel123')
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        mentioned_user.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())
        post_comment = community_member.comment_post(post=post, text='hey @joel123')

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        PostCommentUserMentionNotification = get_post_comment_user_mention_notification_model()
        self.assertFalse(PostCommentUserMentionNotification.objects.filter(
            notification__owner_id=mentioned_user.pk, post_comment_user_mention__post_comment=post_comment).exists())

    def test_close_post_does_not_delete_new_post_notifications_for_staff_and_creator(self):
        """
         should NOT delete new post notifications for staff and creator on close post
        """
        community_post_creator = make_user()
        admin = make_user()
        community_member = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)
        admin.enable_new_post_notifications_for_community_with_name(community_name=community.name)
        community_member.enable_new_post_notifications_for_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        # close post
        self.client.post(url, **headers)

        CommunityNewPostNotification = get_community_new_post_notification_model()
        self.assertTrue(CommunityNewPostNotification.objects.filter(notification__owner_id=admin.pk,
                                                                    post_id=post.pk).exists())
        self.assertFalse(CommunityNewPostNotification.objects.filter(notification__owner_id=community_member.pk,
                                                                    post_id=post.pk).exists())

    def _get_url(self, post):
        return reverse('close-post', kwargs={
            'post_uuid': post.uuid
        })


class PostOpenAPITests(OpenbookAPITestCase):
    """
    PostOpenAPITests APITests
    """

    def test_can_open_post_if_administrator_of_community(self):
        """
         should be able to open post if administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)
        self.assertFalse(parsed_response['is_closed'])

    def test_can_open_post_if_moderator_of_community(self):
        """
         should be able to open post if moderator of a community
        """
        user = make_user()
        admin = make_user()
        moderator = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)
        self.assertFalse(parsed_response['is_closed'])

    def test_cannot_open_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to open post if not moderator/administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)

    def test_logs_open_post_by_administrator_of_community(self):
        """
         should log open post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='OP',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def _get_url(self, post):
        return reverse('open-post', kwargs={
            'post_uuid': post.uuid
        })


class TranslatePostAPITests(OpenbookAPITestCase):
    """
    TranslatePostAPI
    """

    fixtures = [
        'openbook_common/fixtures/languages.json'
    ]

    def test_translate_post_text(self):
        """
        should translate post text and return 200
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='en')
        user.save()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_post = json.loads(response.content)
        self.assertEqual(response_post['translated_text'], 'I am a man 😀. You\'re a woman.')

    def test_cannot_translate_post_text_without_user_language(self):
        """
        should not translate post text and return 400 if user language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_translate_encircled_post(self):
        """
        should not be able to translate encircled post and return 400
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        circle = make_circle(creator=user)
        post = user.create_encircled_post(text=text, circles_ids=[circle.pk])

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_translate_post_text_without_post_comment_language(self):
        """
        should not translate post text and return 400 if post language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)
        post.language = None
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_between_unsupported_translate_pairs(self):
        """
        should return error when translating post between unsupported pairs (Norwegian to arabic) and return 400
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='ar')
        user.save()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=fake.text(max_nb_chars=30))
        post.language = Language.objects.get(code='no')
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_when_text_length_exceeds_max_setting(self):
        """
        should return appropriate error when length of text is more than maximum in settings.py return 400
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='ar')
        user.save()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post.language = Language.objects.get(code='no')
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post):
        return reverse('translate-post', kwargs={
            'post_uuid': post.uuid
        })


class SearchPostParticipantsAPITests(OpenbookAPITestCase):
    """
    SearchPostParticipantsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_retrieves_post_creator_by_username(self):
        """
        should retrieve the post creator by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = post_creator.username[:int(len(post_creator.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_creator.pk:
                found = True

        self.assertTrue(found)

    def test_retrieves_post_creator_by_name(self):
        """
        should retrieve the post creator by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = post_creator.profile.name[:int(len(post_creator.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        for response_participant in response_participants:
            if response_participant['id'] == post_creator.pk:
                found = True
                break
        self.assertTrue(found)

    def test_retrieves_oneself_by_username(self):
        """
        should retrieve the oneself by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = user.username[:int(len(user.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        for response_participant in response_participants:
            if response_participant['id'] == user.pk:
                found = True
                break
        self.assertTrue(found)

    def test_retrieves_oneself_by_name(self):
        """
        should retrieve the oneself by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = user.profile.name[:int(len(user.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        for response_participant in response_participants:
            if response_participant['id'] == user.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_commentator_by_username(self):
        """
        should retrieve a post commentator by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        search_query = post_commentator.username[:int(len(post_commentator.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_commentator_by_name(self):
        """
        should retrieve a post commentator by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        search_query = post_commentator.profile.name[:int(len(post_commentator.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member_by_username(self):
        """
        should retrieve a post community member by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        search_query = post_community_member.username[:int(len(post_community_member.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member_by_name(self):
        """
        should retrieve a post community member by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        search_query = post_community_member.profile.name[:int(len(post_community_member.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_follower_by_username(self):
        """
        should retrieve a follower by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        follower = make_user()
        follower.follow_user(user=user)

        url = self._get_url(post)

        search_query = follower.username[:int(len(follower.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == follower.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_follower_by_name(self):
        """
        should retrieve a follower by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        follower = make_user()
        follower.follow_user(user=user)

        url = self._get_url(post)

        search_query = follower.profile.name[:int(len(follower.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == follower.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_connection_by_username(self):
        """
        should retrieve a connection by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        connection = make_user()
        connection.connect_with_user_with_id(user_id=user.pk)

        user.confirm_connection_with_user_with_id(user_id=connection.pk)

        url = self._get_url(post)

        search_query = connection.username[:int(len(connection.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == connection.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_connection_by_name(self):
        """
        should retrieve a connection by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        connection = make_user()
        connection.connect_with_user_with_id(user_id=user.pk)

        user.confirm_connection_with_user_with_id(user_id=connection.pk)

        url = self._get_url(post)

        search_query = connection.profile.name[:int(len(connection.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == connection.pk:
                found = True
                break

        self.assertTrue(found)

    def _get_url(self, post):
        return reverse('search-post-participants', kwargs={
            'post_uuid': post.uuid
        })


class GetPostParticipantsAPITests(OpenbookAPITestCase):
    """
    SearchPostParticipantsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_retrieves_post_creator(self):
        """
        should retrieve the post creator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        self.assertEqual(response_participants[0]['id'], post_creator.pk)

    def test_retrieves_post_commentator(self):
        """
        should retrieve a post commentator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member(self):
        """
        should retrieve a post community member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def _get_url(self, post):
        return reverse('get-post-participants', kwargs={
            'post_uuid': post.uuid
        })


class PublishPostAPITests(OpenbookAPITestCase):
    """
    PublishPostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_publishing_draft_image_post_should_process_media(self):
        """
        should process draft image post when publishing
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        post = user.create_public_post(image=ImageFile(tmp_file), is_draft=True)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post = Post.objects.get(pk=post.pk)

        self.assertEqual(post.status, Post.STATUS_PROCESSING)

        # Run the process handled by a worker
        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        post.refresh_from_db()

        self.assertEqual(post.status, Post.STATUS_PUBLISHED)

    def test_publishing_draft_video_post_should_process_media(self):
        """
        should process draft video post mp4|3gp|gif media when publishing
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        test_files = get_test_videos()

        for test_file in test_files:
            with open(test_file['path'], 'rb') as file:
                post = user.create_public_post(video=File(file), is_draft=True)

                url = self._get_url(post=post)

                response = self.client.post(url, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                post = Post.objects.get(pk=post.pk)

                self.assertEqual(post.status, Post.STATUS_PROCESSING)

                # Run the process handled by a worker
                get_worker('high', worker_class=SimpleWorker).work(burst=True)

                post.refresh_from_db()

                self.assertEqual(post.status, Post.STATUS_PUBLISHED)

                post_media = post.media.get(type=PostMedia.MEDIA_TYPE_VIDEO)

                post_media_video = post_media.content_object
                self.assertEqual(post_media_video.duration, test_file['duration'])
                self.assertEqual(post_media_video.width, test_file['width'])
                self.assertEqual(post_media_video.height, test_file['height'])
                self.assertTrue(post_media_video.format_set.exists())

    def test_can_publish_draft_text_post(self):
        """
        should be able to publish a draft text post and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = user.create_public_post(text=post_text, is_draft=True)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(Post.objects.filter(pk=post.pk, status=Post.STATUS_PUBLISHED).exists())

    def test_cant_publish_draft_post_with_no_image_nor_text(self):
        """
        should not be able to publish a draft post with no image nor text and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post = user.create_public_post(is_draft=True)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Post.objects.filter(pk=post.pk, status=Post.STATUS_PUBLISHED).exists())

    def test_cant_publish_an_already_published_post(self):
        """
        should not be able to publish an already published post and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = user.create_public_post(text=post_text, is_draft=False)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(Post.objects.filter(pk=post.pk, status=Post.STATUS_PUBLISHED).exists())

    def test_cant_publish_foreign_user_draft_public_post(self):
        """
        should not be able to publish a foreign user draft public post
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = foreign_user.create_public_post(text=post_text, is_draft=True)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(Post.objects.filter(pk=post.pk, status=Post.STATUS_DRAFT).exists())

    def test_cant_publish_foreign_user_draft_community_post(self):
        """
        should not be able to publish a foreign user draft community post
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        community = make_community()
        foreign_user.join_community_with_name(community_name=community.name)

        post = foreign_user.create_community_post(text=post_text, is_draft=True, community_name=community.name)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(Post.objects.filter(pk=post.pk, status=Post.STATUS_DRAFT).exists())

    def test_cant_publish_foreign_user_draft_encircled_post(self):
        """
        should not be able to publish a foreign user draft encircled post
        """
        user = make_user()
        foreign_user = make_user()
        circle = make_circle(creator=foreign_user)

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = foreign_user.create_encircled_post(text=post_text, is_draft=True, circles_ids=[circle.pk])

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(Post.objects.filter(pk=post.pk, status=Post.STATUS_DRAFT))

    def test_publishing_publicly_visible_image_post_with_new_hashtag_should_use_image(self):
        """
        when publishing a publicly visible post with a new hashtag, the hashtag should use the image
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        hashtag_name = make_hashtag_name()

        post_text = '#%s' % hashtag_name

        post = user.create_public_post(text=post_text, image=ImageFile(tmp_file), is_draft=True)

        url = self._get_url(post=post)

        response = self.client.post(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post = Post.objects.get(pk=post.pk)

        self.assertEqual(post.status, Post.STATUS_PROCESSING)

        # Run the process handled by a worker
        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        post.refresh_from_db()

        self.assertEqual(post.status, Post.STATUS_PUBLISHED)

        hashtag = Hashtag.objects.get(name=hashtag_name)
        self.assertTrue(hashtag.has_image())

    def _get_url(self, post):
        return reverse('publish-post', kwargs={
            'post_uuid': post.uuid
        })


class PostStatusAPITests(OpenbookAPITestCase):
    """
    PostStatusAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_retrieve_own_post_status(self):
        """
        should be able to retrieve own post status
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = user.create_public_post(text=post_text, is_draft=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(parsed_response['status'], post.status)

    def test_cant_retrieve_foreign_post_status(self):
        """
        should not be able to retrieve a foreign post status
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        post = foreign_user.create_public_post(text=post_text, is_draft=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _get_url(self, post):
        return reverse('post-status', kwargs={
            'post_uuid': post.uuid
        })
