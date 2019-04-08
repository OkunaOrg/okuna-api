# Create your tests here.
import json
import tempfile
from os import access, F_OK

from PIL import Image
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.images import ImageFile
from django.core.files import File

import logging
import random

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_emoji, make_emoji_group, make_reactions_emoji_group, \
    make_community
from openbook_communities.models import Community
from openbook_notifications.models import PostCommentNotification, PostReactionNotification, Notification
from openbook_posts.models import Post, PostComment, PostReaction

logger = logging.getLogger(__name__)
fake = Faker()


class PostItemAPITests(APITestCase):
    """
    PostItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
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
        should be able to delete image post and file return True
        """
        user = make_user()

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        image = ImageFile(tmp_file)

        post = user.create_public_post(text=make_fake_post_text(), image=image)
        file = post.image.image.file

        user.delete_post_with_id(post.id)

        self.assertFalse(access(file.name, F_OK))

    def test_delete_video_post(self):
        """
        should be able to delete video post and file return True
        """
        user = make_user()

        video = b"video_file_content"
        tmp_file = tempfile.NamedTemporaryFile(suffix='.mp4')
        tmp_file.write(video)
        tmp_file.seek(0)
        video = File(tmp_file)

        post = user.create_public_post(text=make_fake_post_text(), video=video)
        file = post.video.video.file

        user.delete_post_with_id(post.id)

        self.assertFalse(access(file.name, F_OK))

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

    def _get_url(self, post):
        return reverse('post', kwargs={
            'post_uuid': post.uuid
        })


class MutePostAPITests(APITestCase):
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


class UnmutePostAPITests(APITestCase):
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

    def _get_url(self, post):
        return reverse('unmute-post', kwargs={
            'post_uuid': post.uuid
        })


class PostCommentsAPITests(APITestCase):
    """
    PostCommentsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_comment_in_own_post(self):
        """
         should be able to comment in own post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).count() == 1)

    def test_cannot_comment_in_foreign_post(self):
        """
         should not be able to comment in a foreign encircled post and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).count() == 0)

    def test_can_comment_in_connected_user_public_post(self):
        """
         should be able to comment in the public post of a connected user post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        connected_user_post = user_to_connect.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk, text=post_comment_text).count() == 1)

    def test_can_comment_in_connected_user_encircled_post_part_of(self):
        """
          should be able to comment in the encircled post of a connected user which the user is part of and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk, text=post_comment_text).count() == 1)

    def test_cannot_comment_in_connected_user_encircled_post_not_part_of(self):
        """
             should NOT be able to comment in the encircled post of a connected user which the user is NOT part of and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        # Note there is no confirmation of the connection on the other side

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk, text=post_comment_text).count() == 0)

    def test_can_comment_in_user_public_post(self):
        """
          should be able to comment in the public post of any user and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        foreign_user_post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(foreign_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=foreign_user_post.pk, text=post_comment_text).count() == 1)

    def test_cannot_comment_in_followed_user_encircled_post(self):
        """
          should be able to comment in the encircled post of a followed user return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        followed_user_post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(followed_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=followed_user_post.pk, text=post_comment_text).count() == 0)

    def test_commenting_in_foreign_post_creates_notification(self):
        """
         should create a notification when commenting on a foreign post
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertTrue(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                               notification__owner=foreign_user).exists())

    def test_commenting_in_own_post_does_not_create_notification(self):
        """
         should not create a notification when commenting on an own post
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=user).exists())

    def test_commenting_in_commented_post_by_foreign_user_creates_foreign_notification(self):
        """
         should create a notification when a user comments in a post where a foreign user commented before
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        foreign_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        foreign_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertTrue(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                               notification__owner=foreign_user).exists())

    def test_commenting_in_commented_post_by_foreign_user_not_creates_foreign_notification_when_muted(self):
        """
         should NOT create a notification when a user comments in a post where a foreign user commented and muted before
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        foreign_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        foreign_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        foreign_user.mute_post_with_id(post_id=post.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=foreign_user).exists())

    def test_should_retrieve_all_comments_on_public_post(self):
        """
        should retrieve all comments on public post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        url = self._get_url(post)
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [comment['id'] for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == amount_of_post_comments)

        for comment in post_comments:
            self.assertTrue(comment.pk in response_ids)

    def test_should_retrieve_all_comments_on_public_post_with_sort(self):
        """
        should retrieve all comments on public post with sort ascending
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        url = self._get_url(post)
        response = self.client.get(url, {'sort': 'ASC'}, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [comment['id'] for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == amount_of_post_comments)

        for comment in post_comments:
            self.assertTrue(comment.pk in response_ids)

    def test_should_retrieve_comments_less_than_max_id_on_post(self):
        """
        should retrieve comments less than max id for post if param is present
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        random_int = random.randint(3, 9)
        max_id = post_comments[random_int].pk

        url = self._get_url(post)
        response = self.client.get(url, {
            'max_id': max_id
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [comment['id'] for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for returned_id in response_ids:
            self.assertTrue(returned_id < max_id)

    def test_should_retrieve_comments_greater_than_or_equal_to_min_id(self):
        """
        should retrieve comments greater than or equal to min_id for post if param is present
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        random_int = random.randint(3, 9)
        min_id = post_comments[random_int].pk

        url = self._get_url(post)
        response = self.client.get(url, {
            'min_id': min_id
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [comment['id'] for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for returned_id in response_ids:
            self.assertTrue(returned_id >= min_id)

    def test_should_retrieve_comments_slice_for_min_id_and_max_id(self):
        """
        should retrieve comments slice for post comments taking into account min_id and max_id
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 20
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        random_int = random.randint(3, 17)
        min_id = post_comments[random_int].pk
        max_id = min_id
        count_max = 2
        count_min = 3

        url = self._get_url(post)
        response = self.client.get(url, {
            'min_id': min_id,
            'max_id': max_id,
            'count_max': count_max,
            'count_min': count_min
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [int(comment['id']) for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == (count_max + count_min))
        comments_after_min_id = [id for id in response_ids if id >= min_id]
        comments_before_max_id = [id for id in response_ids if id < max_id]
        self.assertTrue(len(comments_after_min_id) == count_min)
        self.assertTrue(len(comments_before_max_id) == count_max)

    def test_should_retrieve_comments_slice_with_sort_for_min_id_and_max_id(self):
        """
        should retrieve comments slice sorted ascending for post comments taking into account min_id and max_id
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 20
        post_comments = []

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            post_comments.append(user.comment_post_with_id(post_id=post.pk, text=post_comment_text))

        random_int = random.randint(3, 17)
        min_id = post_comments[random_int].pk
        max_id = min_id
        count_max = 2
        count_min = 3

        url = self._get_url(post)
        response = self.client.get(url, {
            'min_id': min_id,
            'max_id': max_id,
            'count_max': count_max,
            'count_min': count_min,
            'sort': 'ASC'
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [int(comment['id']) for comment in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == (count_max + count_min))
        self.assertTrue(sorted(response_ids) == response_ids)
        comments_after_min_id = [id for id in response_ids if id >= min_id]
        comments_before_max_id = [id for id in response_ids if id < max_id]
        self.assertTrue(len(comments_after_min_id) == count_min)
        self.assertTrue(len(comments_before_max_id) == count_max)

    def _get_create_post_comment_request_data(self, post_comment_text):
        return {
            'text': post_comment_text
        }

    def _get_url(self, post):
        return reverse('post-comments', kwargs={
            'post_uuid': post.uuid,
        })


class PostCommentItemAPITests(APITestCase):
    """
    PostCommentItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_delete_foreign_comment_in_own_post(self):
        """
          should be able to delete a foreign comment in own post and return 200
        """
        user = make_user()

        commenter = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 0)

    def test_can_delete_community_post_comment_if_mod(self):
        """
         should be able to delete a community post comment if is moderator and return 200
         """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                             community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_can_delete_community_post_comment_if_admin(self):
        """
         should be able to delete a community post comment if is administrator and return 200
         """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_logs_community_post_comment_deleted_by_non_creator(self):
        """
        should create a log when a community post comment was deleted by an admin/moderator
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertTrue(
            community.logs.filter(action_type='RPC', target_user=community_post_commentator, source_user=user).exists())

    def test_can_delete_own_comment_in_foreign_public_post(self):
        """
          should be able to delete own comment in foreign public post and return 200
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 0)

    def test_cannot_delete_foreign_comment_in_foreign_public_post(self):
        """
          should NOT be able to delete foreign comment in foreign public post and return 400
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_can_delete_own_comment_in_connected_user_public_post(self):
        """
          should be able to delete own comment in a connected user public post and return 200
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 0)

    def test_cannot_delete_foreign_comment_in_connected_user_public_post(self):
        """
          should not be able to delete foreign comment in a connected user public post and return 400
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        foreign_user = make_user()

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_can_delete_own_comment_in_connected_user_encircled_post_part_of(self):
        """
           should be able to delete own comment in a connected user encircled post it's part of and return 200
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 0)

    def test_cannot_delete_foreign_comment_in_connected_user_encircled_post_part_of(self):
        """
           should NOT be able to delete foreign comment in a connected user encircled post it's part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_cannot_delete_foreign_comment_in_connected_user_encircled_post_not_part_of(self):
        """
           should NOT be able to delete foreign comment in a connected user encircled post NOT part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_can_delete_own_comment_in_followed_user_public_post(self):
        """
           should be able to delete own comment in a followed user public post and return 200
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 0)

    def test_cannot_delete_foreign_comment_in_followed_user_public_post(self):
        """
           should not be able to delete foreign comment in a followed user public post and return 400
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_cannot_delete_foreign_comment_in_folowed_user_encircled_post(self):
        """
            should not be able to delete foreign comment in a followed user encircled post and return 400
        """
        user = make_user()

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_follow.pk)
        user_to_follow.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).count() == 1)

    def test_post_comment_notification_is_deleted_when_deleting_comment(self):
        """
            should delete the post comment notification when a post comment is deleted
        """
        user = make_user()

        commenter = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(post.pk, text=post_comment_text)

        post_comment_notification = PostCommentNotification.objects.get(post_comment=post_comment,
                                                                        notification__owner=user)
        notification = Notification.objects.get(notification_type=Notification.POST_COMMENT,
                                                object_id=post_comment_notification.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertFalse(PostCommentNotification.objects.filter(pk=post_comment_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_can_edit_own_post_comment_on_own_post(self):
        """
            should be able to edit own post comment
        """

        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())
        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        edited_post_comment_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment.refresh_from_db()
        self.assertTrue(post_comment.text == edited_post_comment_text)
        self.assertTrue(post_comment.is_edited)

    def test_can_edit_own_post_comment_on_others_post(self):
        """
            should be able to edit own post comment on someone else's post
        """

        user = make_user()
        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())
        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        edited_post_comment_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment.refresh_from_db()
        self.assertTrue(post_comment.text == edited_post_comment_text)

    def test_cannot_edit_others_post_comment(self):
        """
            should not be able to edit someone else's comment
        """

        user = make_user()
        commenter = make_user()
        post = user.create_public_post(text=make_fake_post_text())
        original_post_comment_text = make_fake_post_comment_text()
        post_comment = commenter.comment_post_with_id(post.pk, text=original_post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        edited_post_comment_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment.refresh_from_db()
        self.assertTrue(post_comment.text == original_post_comment_text)
        self.assertFalse(post_comment.is_edited)

    def test_cannot_edit_others_community_post_comment_even_if_admin(self):
        """
            should not be able to edit someone else's comment even if community admin
        """

        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        edited_post_comment_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(admin)

        response = self.client.patch(url, {
            'text': edited_post_comment_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment.refresh_from_db()
        self.assertTrue(post_comment.text == original_post_comment_text)

    def _get_url(self, post, post_comment):
        return reverse('post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.pk
        })


class PostReactionsAPITests(APITestCase):
    """
    PostReactionsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_react_to_own_post(self):
        """
         should be able to reaction in own post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_foreign_post(self):
        """
         should not be able to reaction in a foreign encircled post and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 0)

    def test_cannot_react_to_foreign_post_with_non_reaction_emoji(self):
        """
         should not be able to reaction in a post with a non reaction emoji group and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, emoji_id=post_reaction_emoji_id,
                                                    reactor_id=user.pk).count() == 0)

    def test_can_react_to_connected_user_public_post(self):
        """
         should be able to reaction in the public post of a connected user post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        connected_user_post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_can_react_to_connected_user_encircled_post_part_of(self):
        """
          should be able to reaction in the encircled post of a connected user which the user is part of and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_connected_user_encircled_post_not_part_of(self):
        """
             should NOT be able to reaction in the encircled post of a connected user which the user is NOT part of and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        # Note there is no confirmation of the connection on the other side

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(connected_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            PostReaction.objects.filter(post_id=connected_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_can_react_to_user_public_post(self):
        """
          should be able to reaction in the public post of any user and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        foreign_user_post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(foreign_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PostReaction.objects.filter(post_id=foreign_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 1)

    def test_cannot_react_to_followed_user_encircled_post(self):
        """
          should be able to reaction in the encircled post of a followed user return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        followed_user_post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(followed_user_post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            PostReaction.objects.filter(post_id=followed_user_post.pk, emoji_id=post_reaction_emoji_id,
                                        reactor_id=user.pk).count() == 0)

    def test_can_react_to_post_only_once(self):
        """
         should be able to reaction in own post only once, update the old reaction and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        new_post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(new_post_reaction_emoji_id, emoji_group.pk)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostReaction.objects.filter(post_id=post.pk, reactor_id=user.pk).count() == 1)

    def test_reacting_in_foreign_post_creates_notification(self):
        """
         should create a notification when reacting on a foreign post
         """
        user = make_user()
        reactor = make_user()

        headers = make_authentication_headers_for_user(reactor)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertTrue(PostReactionNotification.objects.filter(post_reaction__emoji__id=post_reaction_emoji_id,
                                                                notification__owner=user).exists())

    def test_reacting_in_own_post_does_not_create_notification(self):
        """
         should not create a notification when reacting on an own post
         """
        user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        data = self._get_create_post_reaction_request_data(post_reaction_emoji_id, emoji_group.pk)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostReactionNotification.objects.filter(post_reaction__emoji__id=post_reaction_emoji_id,
                                                                 notification__owner=user).exists())

    def _get_create_post_reaction_request_data(self, emoji_id, emoji_group_id):
        return {
            'emoji_id': emoji_id,
            'group_id': emoji_group_id
        }

    def _get_url(self, post):
        return reverse('post-reactions', kwargs={
            'post_uuid': post.uuid,
        })


class PostReactionItemAPITests(APITestCase):
    """
    PostReactionItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_delete_foreign_reaction_in_own_post(self):
        """
          should be able to delete a foreign reaction in own post and return 200
        """
        user = make_user()

        reactioner = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = reactioner.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                         emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_can_delete_own_reaction_in_foreign_public_post(self):
        """
          should be able to delete own reaction in foreign public post and return 200
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_foreign_public_post(self):
        """
          should NOT be able to delete foreign reaction in foreign public post and return 400
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_own_reaction_in_connected_user_public_post(self):
        """
          should be able to delete own reaction in a connected user public post and return 200
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_connected_user_public_post(self):
        """
          should not be able to delete foreign reaction in a connected user public post and return 400
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        foreign_user = make_user()

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_own_reaction_in_connected_user_encircled_post_part_of(self):
        """
           should be able to delete own reaction in a connected user encircled post it's part of and return 200
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_connected_user_encircled_post_part_of(self):
        """
           should NOT be able to delete foreign reaction in a connected user encircled post it's part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_cannot_delete_foreign_reaction_in_connected_user_encircled_post_not_part_of(self):
        """
           should NOT be able to delete foreign reaction in a connected user encircled post NOT part of and return 400
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_can_delete_own_reaction_in_followed_user_public_post(self):
        """
           should be able to delete own reaction in a followed user public post and return 200
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                   emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 0)

    def test_cannot_delete_foreign_reaction_in_followed_user_public_post(self):
        """
           should not be able to delete foreign reaction in a followed user public post and return 400
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_cannot_delete_foreign_reaction_in_folowed_user_encircled_post(self):
        """
             should not be able to delete foreign reaction in a followed user encircled post and return 400
        """
        user = make_user()

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()
        foreign_user.connect_with_user_with_id(user_to_follow.pk)
        user_to_follow.confirm_connection_with_user_with_id(foreign_user.pk, circles_ids=[circle.pk])

        post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = foreign_user.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                           emoji_group_id=emoji_group.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostReaction.objects.filter(id=post_reaction.pk).count() == 1)

    def test_post_reaction_notification_is_deleted_when_deleting_reaction(self):
        """
        should delete the post reaction notification when a post reaction is deleted
        """
        user = make_user()

        reactioner = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()

        post_reaction_emoji_id = make_emoji(group=emoji_group).pk

        post_reaction = reactioner.react_to_post_with_id(post.pk, emoji_id=post_reaction_emoji_id,
                                                         emoji_group_id=emoji_group.pk)

        post_reaction_notification = PostReactionNotification.objects.get(post_reaction=post_reaction,
                                                                          notification__owner=user)
        notification = Notification.objects.get(notification_type=Notification.POST_REACTION,
                                                object_id=post_reaction_notification.pk)

        url = self._get_url(post_reaction=post_reaction, post=post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertFalse(PostReactionNotification.objects.filter(pk=post_reaction_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def _get_url(self, post, post_reaction):
        return reverse('post-reaction', kwargs={
            'post_uuid': post.uuid,
            'post_reaction_id': post_reaction.pk
        })


class PostReactionsEmojiCountAPITests(APITestCase):
    """
    PostReactionsEmojiCountAPI
    """

    def test_can_retrieve_reactions_emoji_count(self):
        """
        should be able to retrieve a valid reactions emoji count and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        emoji_group = make_reactions_emoji_group()

        emojis_to_react_with = [
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 3
            },
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 7
            },
            {
                'emoji': make_emoji(group=emoji_group),
                'count': 2
            }
        ]

        reactions = {}

        for reaction in emojis_to_react_with:
            id = reaction.get('emoji').pk
            reactions[str(id)] = reaction

        for reaction in emojis_to_react_with:
            for count in range(reaction['count']):
                reactor = make_user()
                emoji = reaction.get('emoji')
                reactor.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, emoji_group_id=emoji_group.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_emojis_counts = json.loads(response.content)

        self.assertTrue(len(response_emojis_counts), len(emojis_to_react_with))

        for response_emoji_count in response_emojis_counts:
            response_emoji_id = response_emoji_count.get('emoji').get('id')
            count = response_emoji_count.get('count')
            reaction = reactions[str(response_emoji_id)]
            reaction_emoji = reaction['emoji']
            self.assertIsNotNone(reaction_emoji)
            reaction_count = reaction['count']
            self.assertEqual(count, reaction_count)

    def _get_url(self, post):
        return reverse('post-reactions-emoji-count', kwargs={
            'post_uuid': post.uuid
        })


class TestPostReactionEmojiGroups(APITestCase):
    """
    PostReactionEmojiGroups API
    """

    def test_can_retrieve_reactions_emoji_groups(self):
        """
         should be able to retrieve post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=True)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)
        response_groups_ids = [group['id'] for group in response_groups]

        self.assertEqual(len(response_groups), len(group_ids))

        for group_id in group_ids:
            self.assertIn(group_id, response_groups_ids)

    def test_cannot_retrieve_non_reactions_emoji_groups(self):
        """
         should not able to retrieve non post reaction emoji groups
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        group_ids = []
        amount_of_groups = 4

        for x in range(amount_of_groups):
            group = make_emoji_group(is_reaction_group=False)
            group_ids.append(group.pk)

        url = self._get_url()
        response = self.client.get(url, **headers)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        response_groups = json.loads(response.content)

        self.assertEqual(len(response_groups), 0)

    def _get_url(self):
        return reverse('posts-emoji-groups')
