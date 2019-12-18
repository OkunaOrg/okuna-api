from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from unittest import mock
import json

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_hashtag_name, make_hashtag
from openbook_common.utils.model_loaders import get_language_model
from openbook_communities.models import Community
from openbook_hashtags.models import Hashtag
from openbook_notifications.models import PostCommentNotification, Notification, PostCommentReplyNotification, \
    PostCommentUserMentionNotification
from openbook_posts.models import PostComment, PostCommentUserMention

logger = logging.getLogger(__name__)
fake = Faker()


class PostCommentItemAPITests(OpenbookAPITestCase):
    """
    PostCommentItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_get_own_post_comment(self):
        """
          should be able to get an own comment in own post and return 200
        """
        user = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_get_foreign_public_post_comment(self):
        """
          should be able to get an own comment in a foreign public post and return 200
        """
        user = make_user()

        post_creator = make_user()

        commenter = make_user()

        foreign_post = post_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(foreign_post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=foreign_post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_get_foreign_encircled_post_comment_part_of(self):
        """
          should be able to get a foreign encircled post comment part of and return 200
        """
        user = make_user()

        post_creator = make_user()
        circle = make_user()

        post_creator.connect_with_user_with_id(user.pk)
        user.confirm_connection_with_user_with_id(post_creator.pk)

        commenter = make_user()

        post_creator.connect_with_user_with_id(commenter.pk)
        commenter.confirm_connection_with_user_with_id(post_creator.pk)

        foreign_post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(foreign_post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=foreign_post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_get_foreign_encircled_post_comment_part_of(self):
        """
          should NOT be able to get a foreign encircled post comment NOT part of and return 400
        """
        user = make_user()

        post_creator = make_user()
        circle = make_user()

        commenter = make_user()

        post_creator.connect_with_user_with_id(commenter.pk)
        commenter.confirm_connection_with_user_with_id(post_creator.pk)

        foreign_post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(foreign_post.pk, text=post_comment_text)

        url = self._get_url(post_comment=post_comment, post=foreign_post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_get_public_community_post_comment(self):
        """
          should be able to get a comment in a public community post and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_get_private_community_post_comment_part_of(self):
        """
          should be able to get a comment in a private community part of post and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(username=community_post_creator.username,
                                                                           community_name=community.name)
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(
            username=community_post_commentator.username,
            community_name=community.name)
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_get_private_community_post_comment_not_part_of(self):
        """
          should NOT be able to get a comment in a private community NOT part of post and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_post_creator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(username=community_post_creator.username,
                                                                           community_name=community.name)
        community_post_creator.join_community_with_name(community_name=community.name)

        community_post_commentator = make_user()
        community_creator.invite_user_with_username_to_community_with_name(
            username=community_post_commentator.username,
            community_name=community.name)
        community_post_commentator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_commentator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                       post_id=post.pk)

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

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

    def test_can_delete_community_post_comment_for_post_with_disabled_comments_if_comment_owner(self):
        """
         should be able to delete a community post comment for post with disabled comments if comment owner
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = commenter.comment_post_with_id(text=make_fake_post_comment_text(),
                                                      post_id=post.pk)

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(commenter)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_can_delete_community_post_comment_with_disabled_comments_if_admin(self):
        """
         should be able to delete a community post comment for post with comments disabled if administrator
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

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_can_delete_community_post_comment_for_post_with_disabled_comments_if_moderator(self):
        """
         should be able to delete a community post comment for post with disabled comments if moderator
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

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_can_delete_community_post_comment_with_closed_post_if_admin(self):
        """
         should be able to delete a community post comment for closed post if administrator
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

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_can_delete_community_post_comment_for_closed_post_if_moderator(self):
        """
         should be able to delete a community post comment for closed post if moderator
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

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_cannot_delete_community_post_comment_for_closed_post_if_comment_owner(self):
        """
         should NOT be able to delete a community post comment for closed post if comment owner
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = commenter.comment_post_with_id(text=make_fake_post_comment_text(),
                                                      post_id=post.pk)

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(commenter)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).exists())

    def test_cannot_delete_own_community_post_comment_for_closed_post_if_post_creator(self):
        """
         should NOT be able to delete own community post comment for closed post if post creator
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_creator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                   post_id=post.pk)

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment, post=post)

        headers = make_authentication_headers_for_user(community_post_creator)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment.pk).exists())

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

        headers = make_authentication_headers_for_user(commenter)
        self.client.delete(url, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(pk=post_comment_notification.pk).exists())
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

    def test_editing_own_post_comment_updates_mentions(self):
        """
        should update mentions when updating text
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_comment_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=post_comment_text)

        post_comment_user_mention = PostCommentUserMention.objects.get(user_id=mentioned_user.pk,
                                                                       post_comment_id=post_comment.pk)

        newly_mentioned_user = make_user()

        post_comment_text = 'Hello @' + newly_mentioned_user.username

        data = {
            'text': post_comment_text
        }

        url = self._get_url(post_comment=post_comment, post=post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertFalse(
            PostCommentUserMention.objects.filter(user_id=mentioned_user.pk, post_comment_id=post_comment.pk).exists())
        self.assertEqual(PostCommentUserMention.objects.filter(user_id=newly_mentioned_user.pk,
                                                               post_comment_id=post_comment.pk).count(), 1)

        new_post_comment_user_mention = PostCommentUserMention.objects.get(user_id=newly_mentioned_user.pk,
                                                                           post_comment_id=post_comment.pk)

        self.assertFalse(
            PostCommentUserMentionNotification.objects.filter(post_comment_user_mention_id=post_comment_user_mention.pk,
                                                              notification__owner_id=mentioned_user.pk,
                                                              notification__notification_type=Notification.POST_COMMENT_USER_MENTION).exists())

        self.assertTrue(PostCommentUserMentionNotification.objects.filter(
            post_comment_user_mention_id=new_post_comment_user_mention.pk,
            notification__owner_id=newly_mentioned_user.pk,
            notification__notification_type=Notification.POST_COMMENT_USER_MENTION).exists())

    def test_editing_text_post_comment_ignores_non_existing_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames when editing a post_comment
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_text())

        fake_username = 'nonexistinguser'
        post_comment_text = 'Hello @' + fake_username

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post_comment=post_comment, post=post)

        response = self.client.patch(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk).count(), 0)

    def test_editing_text_post_comment_ignores_casing_of_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames casings when editing a post_comment
        """
        user = make_user()
        newly_mentioned_user = make_user(username='Miguel')

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_text())

        post_comment_text = 'Hello @miguel'

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post_comment=post_comment, post=post)

        response = self.client.patch(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertTrue(PostCommentUserMention.objects.filter(user_id=newly_mentioned_user.pk,
                                                              post_comment_id=post_comment.pk).exists())

    def test_editing_own_post_comment_does_not_create_double_mentions(self):
        """
        should not create double mentions when editing our own post_comment
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_comment_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=post_comment_text)

        post_comment_user_mention = PostCommentUserMention.objects.get(user_id=mentioned_user.pk,
                                                                       post_comment_id=post_comment.pk)

        data = {
            'text': post_comment_text
        }

        url = self._get_url(post_comment=post_comment, post=post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(
            PostCommentUserMention.objects.filter(user_id=mentioned_user.pk, post_comment_id=post_comment.pk).count(),
            1)
        new_post_comment_user_mention = PostCommentUserMention.objects.get(user_id=mentioned_user.pk,
                                                                           post_comment_id=post_comment.pk,
                                                                           id=post_comment_user_mention.pk)
        self.assertEqual(new_post_comment_user_mention.pk, post_comment_user_mention.pk)

    def test_editing_own_post_comment_comment_with_hashtag_creates_hashtag_if_not_exist(self):
        """
        when editing a post comment with a hashtag, should create  it if not exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag_name = make_hashtag_name()
        post_comment_text = 'One hashtag #' + hashtag_name

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=post_comment_text)

        new_hashtag_name = make_hashtag_name()

        new_post_comment_commenttext = 'Another hashtag #' + new_hashtag_name

        data = {
            'text': new_post_comment_commenttext
        }

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        created_hashtag = Hashtag.objects.get(name=new_hashtag_name)
        self.assertTrue(post_comment.hashtags.filter(pk=created_hashtag.pk).exists())
        self.assertEqual(post_comment.hashtags.all().count(), 1)

    def test_editing_own_post_comment_comment_with_hashtag_updates_to_existing_hashtag_exists(self):
        """
        when editing a post comment with a hashtag, should update to it if exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()
        post_comment_text = 'One hashtag #' + hashtag.name

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=post_comment_text)

        new_hashtag = make_hashtag()

        new_post_comment_commenttext = 'Another hashtag #' + new_hashtag.name

        data = {
            'text': new_post_comment_commenttext
        }

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertTrue(post_comment.hashtags.filter(pk=new_hashtag.pk).exists())
        self.assertEqual(post_comment.hashtags.all().count(), 1)

    def test_editing_own_post_comment_comment_with_hashtag_does_not_create_double_hashtags(self):
        """
        when editing a post comment with a hashtag, should not create duplicate hashtags
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()
        post_comment_text = 'One hashtag #' + hashtag.name

        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=post_comment_text)

        new_post_comment_commenttext = 'Same hashtag #' + hashtag.name

        data = {
            'text': new_post_comment_commenttext
        }

        url = self._get_url(post_comment=post_comment, post=post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(post_comment.hashtags.filter(name=hashtag.name).count(), 1)
        self.assertEqual(post_comment.hashtags.all().count(), 1)

    @mock.patch('openbook_posts.models.get_language_for_text')
    def test_editing_own_post_comment_updates_language_of_comment(self, get_language_for_text_call):
        """
            should update language of comment when editing post comment
        """
        Language = get_language_model()
        get_language_for_text_call.return_value = Language.objects.get(id=1)
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
        get_language_for_text_call.assert_called_with(edited_post_comment_text)

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

    def test_cannot_edit_post_comment_if_comments_disabled(self):
        """
            should not be able to edit own comment if comments are disabled
        """

        admin = make_user()
        user = make_user()
        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        post.comments_enabled = False
        post.save()

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

    def test_cannot_edit_post_comment_if_post_closed_and_not_not_post_creator(self):
        """
            should NOT be able to edit own comment if post is closed and not post creator
        """

        admin = make_user()
        user = make_user()
        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = admin.create_community_post(community.name, text=make_fake_post_text())

        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        post.is_closed = True
        post.save()

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

    def test_cannot_edit_post_comment_if_post_closed_and_post_creator(self):
        """
            should NOT be able to edit own comment if post is closed even if post creator
        """

        admin = make_user()
        user = make_user()
        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        original_post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=original_post_comment_text)

        post.is_closed = True
        post.save()

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

    # Post Comments that are replies

    def test_can_delete_foreign_comment_reply_in_own_post(self):
        """
          should be able to delete a foreign comment reply in own post and return 200
        """
        user = make_user()

        commenter = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_reply_text = make_fake_post_comment_text()

        post_comment = commenter.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = commenter.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=post_comment_reply_text)

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_if_mod(self):
        """
         should be able to delete a community post comment reply if is moderator and return 200
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_if_admin(self):
        """
         should be able to delete a community post comment reply if is administrator and return 200
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_for_post_with_disabled_comments_if_comment_owner(self):
        """
         should be able to delete a community post comment reply for post with disabled comments if comment owner
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = commenter.comment_post_with_id(text=make_fake_post_comment_text(),
                                                      post_id=post.pk)
        post_comment_reply = \
            commenter.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                  post_uuid=post.uuid,
                                                                  text=make_fake_post_comment_text())

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(commenter)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_with_disabled_comments_if_admin(self):
        """
         should be able to delete a community post comment reply for post with comments disabled if administrator
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_for_post_with_disabled_comments_if_moderator(self):
        """
         should be able to delete a community post comment reply for post with disabled comments if moderator
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_with_closed_post_if_admin(self):
        """
         should be able to delete a community post comment reply for closed post if administrator
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_can_delete_community_post_comment_reply_for_closed_post_if_moderator(self):
        """
         should be able to delete a community post comment reply for closed post if moderator
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_cannot_delete_community_post_comment_reply_for_closed_post_if_comment_owner(self):
        """
         should NOT be able to delete a community post comment reply for closed post if comment owner
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = commenter.comment_post_with_id(text=make_fake_post_comment_text(),
                                                      post_id=post.pk)
        post_comment_reply = \
            commenter.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                  post_uuid=post.uuid,
                                                                  text=make_fake_post_comment_text())

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(commenter)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_cannot_delete_own_community_post_comment_reply_for_closed_post_if_post_creator(self):
        """
         should NOT be able to delete own community post comment reply for closed post if post creator
         """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)

        user.join_community_with_name(community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = community_post_creator.comment_post_with_id(text=make_fake_post_comment_text(),
                                                                   post_id=post.pk)
        post_comment_reply = \
            community_post_creator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                               post_uuid=post.uuid,
                                                                               text=make_fake_post_comment_text())

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(community_post_creator)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).exists())

    def test_logs_community_post_comment_reply_deleted_by_non_creator(self):
        """
        should create a log when a community post comment reply was deleted by an admin/moderator
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
        post_comment_reply = \
            community_post_commentator.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertTrue(
            community.logs.filter(action_type='RPCR',
                                  target_user=community_post_commentator,
                                  source_user=user).exists())

    def test_can_delete_own_comment_reply_in_foreign_public_post(self):
        """
          should be able to delete own comment reply in foreign public post and return 200
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 0)

    def test_cannot_delete_foreign_comment_reply_in_foreign_public_post(self):
        """
          should NOT be able to delete foreign comment reply in foreign public post and return 400
        """
        user = make_user()

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_can_delete_own_comment_reply_in_connected_user_public_post(self):
        """
          should be able to delete own comment reply in a connected user public post and return 200
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 0)

    def test_cannot_delete_foreign_comment_reply_in_connected_user_public_post(self):
        """
          should not be able to delete foreign comment reply in a connected user public post and return 400
        """
        user = make_user()

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk)

        foreign_user = make_user()

        post = user_to_connect.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_can_delete_own_comment_reply_in_connected_user_encircled_post_part_of(self):
        """
           should be able to delete own comment reply in a connected user encircled post it's part of and return 200
         """
        user = make_user()

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 0)

    def test_cannot_delete_foreign_comment_reply_in_connected_user_encircled_post_part_of(self):
        """
           should NOT be able to delete foreign comment reply in a connected user encircled post it's part of and return 400
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
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_cannot_delete_foreign_comment_reply_in_connected_user_encircled_post_not_part_of(self):
        """
           should NOT be able to delete foreign comment reply in a connected user encircled post NOT part of and return 400
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
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_can_delete_own_comment_reply_in_followed_user_public_post(self):
        """
           should be able to delete own comment reply in a followed user public post and return 200
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 0)

    def test_cannot_delete_foreign_comment_reply_in_followed_user_public_post(self):
        """
           should not be able to delete foreign comment reply in a followed user public post and return 400
         """
        user = make_user()

        user_to_follow = make_user()

        user.follow_user_with_id(user_to_follow.pk)

        foreign_user = make_user()

        post = user_to_follow.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = foreign_user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_cannot_delete_foreign_comment_reply_in_folowed_user_encircled_post(self):
        """
            should not be able to delete foreign comment reply in a followed user encircled post and return 400
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
        post_comment_reply = foreign_user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                      post_uuid=post.uuid,
                                                                                      text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(id=post_comment_reply.pk).count() == 1)

    def test_post_comment_reply_notification_is_deleted_when_deleting_comment(self):
        """
            should delete the post comment reply notification when a post comment is deleted
        """
        user = make_user()

        commenter = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        post_comment = user.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = commenter.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=make_fake_post_comment_text())

        post_comment_reply_notification = PostCommentReplyNotification.objects.get(post_comment=post_comment_reply,
                                                                                   notification__owner=user)

        notification = Notification.objects.get(notification_type=Notification.POST_COMMENT_REPLY,
                                                object_id=post_comment_reply_notification.pk)

        url = self._get_url(post_comment=post_comment_reply, post=post)

        headers = make_authentication_headers_for_user(commenter)
        self.client.delete(url, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(pk=post_comment_reply_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_can_edit_own_post_comment_reply_on_own_post(self):
        """
            should be able to edit own post comment reply
        """

        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == edited_comment_reply_text)
        self.assertTrue(post_comment_reply.is_edited)

    def test_can_edit_own_post_comment_reply_on_others_post_comment(self):
        """
            should be able to edit own post comment reply on someone else's post comment
        """

        user = make_user()
        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_creator.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=make_fake_post_comment_text())

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_post_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == edited_post_comment_reply_text)

    def test_cannot_edit_others_post_comment_reply(self):
        """
            should not be able to edit someone else's comment reply
        """

        user = make_user()
        commenter = make_user()
        post = user.create_public_post(text=make_fake_post_text())
        original_post_comment_reply_text = make_fake_post_comment_text()
        post_comment = commenter.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = commenter.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                                   post_uuid=post.uuid,
                                                                                   text=original_post_comment_reply_text)

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_post_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == original_post_comment_reply_text)
        self.assertFalse(post_comment_reply.is_edited)

    def test_cannot_edit_post_comment_reply_if_comments_disabled(self):
        """
            should not be able to edit own comment reply if comments are disabled
        """

        admin = make_user()
        user = make_user()
        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        original_post_comment_reply_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=original_post_comment_reply_text)

        post.comments_enabled = False
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_post_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == original_post_comment_reply_text)
        self.assertFalse(post_comment_reply.is_edited)

    def test_cannot_edit_post_comment_reply_if_post_closed_and_not_not_post_creator(self):
        """
            should NOT be able to edit own comment reply if post is closed and not post creator
        """

        admin = make_user()
        user = make_user()
        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = admin.create_community_post(community.name, text=make_fake_post_text())

        original_post_comment_reply_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                                              post_uuid=post.uuid,
                                                                              text=original_post_comment_reply_text)

        post.is_closed = True
        post.save()

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_post_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(user)

        response = self.client.patch(url, {
            'text': edited_post_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == original_post_comment_reply_text)
        self.assertFalse(post_comment_reply.is_edited)

    def _get_url(self, post, post_comment):
        return reverse('post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.pk
        })


class MutePostCommentAPITests(OpenbookAPITestCase):
    """
    MutePostCommentAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_mute_own_post_comment(self):
        """
        should be able to mute own post comment and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_cant_mute_own_post_comment_if_already_muted(self):
        """
        should not be able to mute own post comment if already muted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        user.mute_post_comment_with_id(post_comment.pk)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_foreign_post_comment_if_public_post_comment(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_public_post(text=make_fake_post_text())
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_cannot_mute_foreign_post_comment_if_encircled_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(),
                                                  circles_ids=[circle.pk])
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_foreign_post_comment_if_part_of_encircled_post_comment(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(),
                                                  circles_ids=[circle.pk])
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        foreign_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=foreign_user.pk)

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_community_post_comment_if_public(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(),
                                                  community_name=community.name)
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_closed_community_post_comment(self):
        """
        should be able to mute closed post comment if not admin/mod or post comment creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(),
                                                  community_name=community.name)
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_closed_community_post_comment_if_creator(self):
        """
        should be able to mute closed post comment if post_comment creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_closed_community_post_comment_administrator(self):
        """
        should be able to mute closed post comment if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(admin.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_closed_community_post_comment_if_moderator(self):
        """
        should be able to mute closed post comment if moderator in community
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
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(moderator.has_muted_post_comment_with_id(post_comment.pk))

    def test_cant_mute_community_post_comment_if_private_and_not_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(),
                                                  community_name=community.name)
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_mute_community_post_comment_if_private_and_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(),
                                                  community_name=community.name)
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())

        foreign_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_comment_with_id(post_comment.pk))

    def _get_url(self, post, post_comment):
        return reverse('mute-post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.id,
        })


class UnmutePostCommentAPITests(OpenbookAPITestCase):
    """
    UnmutePostCommentAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_unmute_own_post_comment(self):
        """
        should be able to unmute own post comment and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        user.mute_post_comment_with_id(post_comment.pk)

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_cant_unmute_own_post_comment_if_already_unmuted(self):
        """
        should not be able to unmute own post comment if already unmuted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_unmute_closed_community_post_comment(self):
        """
        should be able to unmute closed post comment if not admin/mod or post comment creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(),
                                                  community_name=community.name)
        post_comment = foreign_user.comment_post(post=post, text=make_fake_post_comment_text())
        user.mute_post_comment_with_id(post_comment.pk)
        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_unmute_closed_community_post_comment_if_creator(self):
        """
        should be able to unmute closed post comment if post_comment creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())
        user.mute_post_comment_with_id(post_comment.pk)
        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_unmute_closed_community_post_comment_administrator(self):
        """
        should be able to unmute closed post comment if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())
        admin.mute_post_comment_with_id(post_comment.pk)
        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(admin.has_muted_post_comment_with_id(post_comment.pk))

    def test_can_unmute_closed_community_post_comment_if_moderator(self):
        """
        should be able to unmute closed post comment if moderator in community
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
        post = user.create_community_post(text=make_fake_post_text(),
                                          community_name=community.name)
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())
        moderator.mute_post_comment_with_id(post_comment.pk)
        post_comment.is_closed = True
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(moderator.has_muted_post_comment_with_id(post_comment.pk))

    def _get_url(self, post, post_comment):
        return reverse('unmute-post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.id,
        })


class TranslatePostCommentAPITests(OpenbookAPITestCase):
    """
    TranslatePostCommentAPI
    """

    fixtures = [
        'openbook_common/fixtures/languages.json'
    ]

    def test_translate_post_comment_text(self):
        """
        should translate post comment text and return 200
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='en')
        user.save()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=text)

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_post = json.loads(response.content)

        self.assertEqual(response_post['translated_text'], 'I am a man 😀. You\'re a woman.')

    def test_cannot_translate_post_comment_text_without_user_language(self):
        """
        should not translate post comment text and return 400 if user language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=text)

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_translate_comment_in_encircled_post(self):
        """
        should not translate post comment text in an encircled post and return 400
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        circle = make_circle(creator=user)
        post = user.create_encircled_post(text=text, circles_ids=[circle.pk])
        post_comment = user.comment_post(post=post, text=text)

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_translate_post_comment_text_without_post_comment_language(self):
        """
        should not translate post comment text and return 400 if post comment language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=text)
        post_comment.language = None
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_between_unsupported_translate_pairs(self):
        """
        should return error using aws translate when translating comment between unsupported pairs (Norwegian to arabic) and return 400
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='ar')
        user.save()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post(post=post, text=fake.text(max_nb_chars=30))
        post_comment.language = Language.objects.get(code='no')
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)
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
        post_comment = user.comment_post(post=post, text=make_fake_post_comment_text())
        post_comment.language = Language.objects.get(code='no')
        post_comment.save()

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post, post_comment):
        return reverse('translate-post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.id,
        })
