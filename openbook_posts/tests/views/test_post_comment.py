# Create your tests here.
import json
import random
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_private_community
from openbook_notifications.models import PostCommentNotification, Notification, PostCommentReplyNotification
from openbook_posts.models import PostComment

logger = logging.getLogger(__name__)
fake = Faker()


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
        post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_creator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
            community_post_commentator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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

        post_comment = commenter.comment_post_with_id(post.pk, text=post_comment_text)
        post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
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

    def test_cannot_edit_others_community_post_comment_even_if_admin(self):
        """
            should not be able to edit someone else's comment even if community admin
        """

        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        original_post_comment_reply_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                            text=original_post_comment_reply_text)

        url = self._get_url(post_comment=post_comment_reply, post=post)

        edited_post_comment_reply_text = make_fake_post_comment_text()
        headers = make_authentication_headers_for_user(admin)

        response = self.client.patch(url, {
            'text': edited_post_comment_reply_text
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_comment_reply.refresh_from_db()
        self.assertTrue(post_comment_reply.text == original_post_comment_reply_text)

    def _get_url(self, post, post_comment):
        return reverse('post-comment', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.pk
        })


class PostCommentRepliesAPITests(APITestCase):

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_retrieve_comment_replies_from_public_community_post(self):
        """
        should be able to retrieve comment replies for posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_replies = 5
        reply_ids = []
        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(
                post_comment_id=post_comment.pk,
                text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_closed_public_community_post_if_creator(self):
        """
        should be able to retrieve comment replies for closed posts if creator
        """

        post_creator = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(post_creator)
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_closed_public_community_post_if_administrator(self):
        """
        should be able to retrieve comment replies for closed posts if administrator
        """

        post_creator = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comments_from_closed_public_community_post_if_moderator(self):
        """
        should be able to retrieve comments for closed posts if moderator
        """

        post_creator = make_user()
        admin = make_user()
        moderator = make_user()
        headers = make_authentication_headers_for_user(moderator)
        community = make_community(creator=admin)

        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username, community_name=community.name)

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_cant_retrieve_comment_replies_from_private_community_post(self):
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_private_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        post_creator.invite_user_with_username_to_community_with_name(username=commenter.username,
                                                                      community_name=community.name)
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_comment_replies_from_private_community_part_of_post(self):
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_private_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        post_creator.invite_user_with_username_to_community_with_name(username=commenter.username,
                                                                      community_name=community.name)
        commenter.join_community_with_name(community_name=community.name)
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_public_post(self):
        """
         should be able to retrieve the comment replies from an own public post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_own_public_post(self):
        """
         should be able to retrieve the comment replies from an own public post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_own_encircled_post(self):
        """
         should be able to retrieve the comment replies from an own encircled post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        circle = make_circle(creator=user)
        post = user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        commenter.connect_with_user_with_id(user.pk)
        user.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_can_retrieve_comment_replies_from_encircled_post_part_of(self):
        """
         should be able to retrieve the comment replies from an encircled post part of and return 200
         """
        post_creator = make_user()
        circle = make_circle(creator=post_creator)
        user = make_user()

        user.connect_with_user_with_id(post_creator.pk)
        post_creator.confirm_connection_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])

        post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_replies = 5
        reply_ids = []

        commenter = make_user()
        commenter.connect_with_user_with_id(post_creator.pk)
        post_creator.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            post_comment_reply = commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                     text=make_fake_post_comment_text())
            reply_ids.append(post_comment_reply.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), amount_of_replies)

        for reply in response_comment_replies:
            reply_id = reply.get('id')
            self.assertIn(reply_id, reply_ids)

    def test_cannot_retrieve_comment_replies_from_encircled_post_not_part_of(self):
        """
         should not be able to retrieve the comment replies from an encircled post not part of and return 200
         """
        post_creator = make_user()
        circle = make_circle(creator=post_creator)
        user = make_user()

        post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_replies = 5
        commenter = make_user()
        commenter.connect_with_user_with_id(post_creator.pk)
        post_creator.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])
        post_comment = commenter.comment_post(post=post, text=make_fake_post_text())

        for i in range(0, amount_of_replies):
            commenter.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                text=make_fake_post_comment_text())

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_comment_replies_from_blocked_user(self):
        """
         should not be able to retrieve the comment replies from a blocked user
         """
        user = make_user()

        post_creator = make_user()
        blocked_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        post_comment = blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        blocked_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), 0)

    def test_cannot_retrieve_comment_replies_from_blocking_user(self):
        """
         should not be able to retrieve the comment replies from a blocking user
         """
        user = make_user()

        post_creator = make_user()
        blocking_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        post_comment = blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        blocking_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())
        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), 0)

    def test_cannot_retrieve_comment_replies_from_blocked_user_in_a_community(self):
        """
         should not be able to retrieve the comment replies from a blocked user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocked_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        blocked_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), 0)

    def test_cannot_retrieve_comment_replies_from_blocking_user_in_a_community(self):
        """
         should not be able to retrieve the comment replies from a blocking user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocking_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        blocking_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                text=make_fake_post_comment_text())

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(len(response_comment_replies), 0)

    def test_can_retrieve_comment_replies_from_blocked_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the comment replies from a blocked user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocked_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post_comment_reply = blocked_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(1, len(response_comment_replies))

        self.assertEqual(response_comment_replies[0]['id'], post_comment_reply.pk)

    def test_can_retrieve_comment_replies_from_blocking_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the comment replies from a blocking user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocking_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post_comment_reply = blocking_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                text=make_fake_post_comment_text())

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post, post_comment)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comment_replies = json.loads(response.content)

        self.assertEqual(1, len(response_comment_replies))

        self.assertEqual(response_comment_replies[0]['id'], post_comment_reply.pk)

    def test_can_reply_to_comment_in_own_post(self):
        """
         should be able to reply to comment in own post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(parent_comment_id=post_comment.pk,
                                                   post_id=post.pk,
                                                   text=reply_comment_text).count() == 1)

    def test_cannot_reply_to_a_reply_in_post(self):
        """
         should NOT be able to reply to an existing reply in post
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                            text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment_reply)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(parent_comment_id=post_comment_reply.pk,
                                                    post_id=post.pk,
                                                    text=reply_comment_text).exists())

    def test_cannot_reply_comment_in_foreign_post(self):
        """
         should not be able to reply comment in a foreign encircled post and return 400
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
        post_comment = foreign_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=reply_comment_text).count() == 0)

    def test_can_reply_comment_in_connected_user_public_post(self):
        """
         should be able to reply comment in the public post of a connected user post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()

        user.connect_with_user_with_id(user_to_connect.pk)

        connected_user_post = user_to_connect.create_public_post(text=make_fake_post_text())
        post_comment = user_to_connect.comment_post_with_id(post_id=connected_user_post.pk, text=make_fake_post_comment_text())
        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(connected_user_post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk, text=reply_comment_text).count() == 1)

    def test_cannot_comment_reply_in_blocked_user_post(self):
        """
          should not be able to comment reply in a blocked user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())
        post_comment = user_to_block.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.block_user_with_id(user_id=user_to_block.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_cannot_comment_reply_in_blocking_user_post(self):
        """
          should not be able to comment reply in a blocking user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_cannot_comment_reply_in_blocked_user_community_post(self):
        """
          should not be able to comment reply in a blocked user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_cannot_comment_reply_in_blocking_user_community_post(self):
        """
          should not be able to comment reply in a blocking user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=reply_comment_text).exists())

    def test_can_comment_reply_in_blocked_community_staff_member_post(self):
        """
          should be able to comment reply in a blocked community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=reply_comment_text).count() == 1)

    def test_can_comment_reply_in_blocking_community_staff_member_post(self):
        """
          should be able to comment reply in a blocking community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=reply_comment_text).count() == 1)

    def test_owner_cannot_comment_reply_in_community_post_with_disabled_comments(self):
        """
         should not be able to comment reply in the community post with comments disabled even if owner of post
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.comments_enabled = False
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_foreign_user_cannot_reply_comment_in_community_post_with_disabled_comments(self):
        """
         should not be able to reply comment in the community post with comments disabled even if foreign user
         """
        user = make_user()
        foreign_user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(foreign_user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.comments_enabled = False
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_administrator_can_comment_reply_in_community_post_with_disabled_comments(self):
        """
         should be able to comment reply in the community post with comments disabled if administrator
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.comments_enabled = False
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment_reply = PostComment.objects.get(post_id=post.pk,
                                                     parent_comment_id=post_comment.pk,
                                                     text=reply_comment_text,
                                                     commenter=admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).exists())
        self.assertEqual(response_id, post_comment_reply.id)

    def test_moderator_can_comment_reply_in_community_post_with_disabled_comments(self):
        """
         should be able to comment reply in the community post with comments disabled if moderator
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
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.comments_enabled = False
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment_reply = PostComment.objects.get(post_id=post.pk,
                                               parent_comment_id=post_comment.pk,
                                               text=reply_comment_text, commenter=moderator)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).exists())
        self.assertEqual(response_id, post_comment_reply.id)

    def test_owner_can_comment_reply_on_closed_community_post(self):
        """
         should be able to comment reply in the community post which is closed
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.is_closed = True
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).exists())

    def test_foreign_user_cannot_comment_reply_on_closed_community_post(self):
        """
         should not be able to comment reply in the community post that is closed
         """
        user = make_user()
        foreign_user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(foreign_user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.is_closed = True
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk,
                                                    parent_comment_id=post_comment.pk,
                                                    text=reply_comment_text).exists())

    def test_moderator_can_comment_reply_on_closed_community_post(self):
        """
         should be able to comment reply on the community post which is closed if moderator
         """
        user = make_user()
        admin = make_user()
        moderator = make_user()

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username, community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.comments_enabled = False
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment_reply = PostComment.objects.get(post_id=post.pk,
                                               parent_comment_id=post_comment.pk,
                                               text=reply_comment_text,
                                               commenter=moderator)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).exists())
        self.assertEqual(response_id, post_comment_reply.id)

    def test_administrator_can_comment_reply_on_closed_community_post(self):
        """
         should be able to comment reply in the community post which is closed if administrator
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        post.is_closed = True
        post.save()
        reply_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment_reply = PostComment.objects.get(post_id=post.pk,
                                                     parent_comment_id=post_comment.pk,
                                                     text=reply_comment_text, commenter=admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).exists())
        self.assertEqual(response_id, post_comment_reply.id)

    def test_can_comment_reply_in_connected_user_encircled_post_part_of(self):
        """
          should be able to comment reply in the encircled post of a connected user which the user is part of and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        user_to_connect.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
        post_comment = user_to_connect.comment_post_with_id(post_id=connected_user_post.pk, text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(connected_user_post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).count() == 1)

    def test_cannot_comment_reply_in_connected_user_encircled_post_not_part_of(self):
        """
             should NOT be able to comment reply in the encircled post of a connected user which the user is NOT part of and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_connect = make_user()
        circle = make_circle(creator=user_to_connect)

        user.connect_with_user_with_id(user_to_connect.pk)
        # Note there is no confirmation of the connection on the other side

        connected_user_post = user_to_connect.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
        post_comment = user_to_connect.comment_post_with_id(post_id=connected_user_post.pk, text=make_fake_post_comment_text())
        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(connected_user_post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(PostComment.objects.filter(post_id=connected_user_post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).count() == 0)

    def test_can_comment_reply_in_user_public_post(self):
        """
          should be able to comment reply in the public post of any user and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        foreign_user_post = foreign_user.create_public_post(text=make_fake_post_text())
        post_comment = foreign_user.comment_post_with_id(post_id=foreign_user_post.pk, text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(foreign_user_post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=foreign_user_post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).count() == 1)

    def test_cannot_comment_reply_in_followed_user_encircled_post(self):
        """
          should be able to comment reply in the encircled post of a followed user return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_follow = make_user()
        circle = make_circle(creator=user_to_follow)

        user.follow_user_with_id(user_to_follow.pk)

        followed_user_post = user_to_follow.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
        post_comment = user_to_follow.comment_post_with_id(post_id=followed_user_post.pk, text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(followed_user_post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=followed_user_post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=reply_comment_text).count() == 0)

    def test_cannot_comment_reply_in_post_from_community_banned_from(self):
        """
          should not be able to comment reply in the post of a community banned from and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_comment = community_owner.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.comment_post(post=post, text=make_fake_post_comment_text())

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        new_reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(new_reply_comment_text)

        url = self._get_url(post, post_comment)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk,
                                                   parent_comment_id=post_comment.pk,
                                                   text=new_reply_comment_text).count() == 0)

    def test_cannot_retrieve_comment_of_own_soft_deleted_post(self):
        """
        should not be able to retrieve the comments of a soft deleted post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post.soft_delete()

        url = self._get_url(post_comment=post_comment, post=post)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cannot_retrieve_comment_of_foreign_soft_deleted_post(self):
        """
        should not be able to retrieve the comments of a soft deleted post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = user.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post.soft_delete()

        url = self._get_url(post=post, post_comment=post_comment)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_commenting_reply_in_foreign_post_creates_notification(self):
        """
         should create a notification when replying to comment on a foreign post
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()

        post = foreign_user.create_public_post(text=make_fake_post_text())
        post_comment = foreign_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                       text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertTrue(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                    notification__owner=foreign_user).exists())

    def test_commenting_reply_in_own_post_does_not_create_notification(self):
        """
         should not create a notification when commenting reply on own post
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                       text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                     notification__owner=user).exists())

    def test_commenting_reply_in_commented_post_by_foreign_user_creates_foreign_notification(self):
        """
         should create a notification when a user comments reply in a post where a foreign user commented before
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        foreign_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_creator.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertTrue(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                    notification__owner=foreign_user).exists())

    def test_commenting_reply_in_commented_post_by_foreign_user_not_creates_foreign_notification_when_muted(self):
        """
         should NOT create a notification when a user comments reply in a post where a foreign user commented and muted before
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()

        foreign_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_creator.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())
        foreign_user.mute_post_with_id(post_id=post.pk)

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                     notification__owner=foreign_user).exists())

    def test_reply_in_community_post_by_foreign_user_does_not_create_foreign_notification_when_closed(self):
        """
         should NOT create a notification when a creator comments reply in a CLOSED community post where a foreign user commented
         """
        post_creator = make_user()
        admin = make_user()
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        foreign_user = make_user()
        foreign_user.join_community_with_name(community_name=community.name)
        post_comment = post_creator.comment_post(post=post, text=make_fake_post_text())
        # subscribe to notifications
        foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())
        # post will be closed now
        post.is_closed = True
        post.save()

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)
        headers = make_authentication_headers_for_user(post_creator)
        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                     notification__owner=foreign_user).exists())

    def test_reply_in_community_post_by_admin_does_create_notification_when_closed(self):
        """
         should create a notification to a community post creator when an admin comments in a CLOSED post
         """
        post_creator = make_user()
        admin = make_user()
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = post_creator.comment_post(post=post, text=make_fake_post_text())
        # subscribe to notifications
        post_creator.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())
        # post will be closed now
        post.is_closed = True
        post.save()

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)
        headers = make_authentication_headers_for_user(admin)
        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertTrue(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                    notification__owner=post_creator).exists())

    def test_comment_reply_in_an_encircled_post_with_a_user_removed_from_the_circle_not_notifies_it(self):
        """
         should not create a comment reply notification for a user that has been been removed from an encircled post circle
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_owner = make_user()
        foreign_user = make_user()
        circle = make_circle(creator=post_owner)

        user.connect_with_user_with_id(user_id=post_owner.pk)
        post_owner.confirm_connection_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])

        foreign_user.connect_with_user_with_id(user_id=post_owner.pk)
        post_owner.confirm_connection_with_user_with_id(user_id=foreign_user.pk, circles_ids=[circle.pk])

        post = post_owner.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
        post_comment = post_owner.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        # Comment Reply so we "subscribe" for notifications
        foreign_user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                               text=make_fake_post_comment_text())

        # Remove them from the circles
        post_owner.update_connection_with_user_with_id(user_id=foreign_user.pk,
                                                       circles_ids=[post_owner.connections_circle_id])

        reply_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(reply_comment_text)

        url = self._get_url(post, post_comment)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(post_comment__text=reply_comment_text,
                                                                     notification__owner=foreign_user).exists())

    def test_should_retrieve_all_comment_replies_on_public_post(self):
        """
        should retrieve all comment replies on public post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 10
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        url = self._get_url(post, post_comment)
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [reply['id'] for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == amount_of_replies)

        for comment in comment_replies:
            self.assertTrue(comment.pk in response_ids)

    def test_should_retrieve_all_comment_replies_on_public_post_with_sort(self):
        """
        should retrieve all comment replies on public post with sort ascending
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 10
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        url = self._get_url(post, post_comment)
        response = self.client.get(url, {'sort': 'ASC'}, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [reply['id'] for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == amount_of_replies)

        for comment in comment_replies:
            self.assertTrue(comment.pk in response_ids)

    def test_should_retrieve_comment_replies_less_than_max_id_on_post(self):
        """
        should retrieve comment replies less than max id for post if param is present
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 10
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        random_int = random.randint(3, 9)
        max_id = comment_replies[random_int].pk

        url = self._get_url(post, post_comment)
        response = self.client.get(url, {
            'max_id': max_id
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [reply['id'] for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for returned_id in response_ids:
            self.assertTrue(returned_id < max_id)

    def test_should_retrieve_comment_replies_greater_than_or_equal_to_min_id(self):
        """
        should retrieve comment replies greater than or equal to min_id for post if param is present
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 10
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        random_int = random.randint(3, 9)
        min_id = comment_replies[random_int].pk

        url = self._get_url(post, post_comment)
        response = self.client.get(url, {
            'min_id': min_id
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [reply['id'] for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for returned_id in response_ids:
            self.assertTrue(returned_id >= min_id)

    def test_should_retrieve_comment_replies_slice_for_min_id_and_max_id(self):
        """
        should retrieve comment replies slice for post comments taking into account min_id and max_id
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 20
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        random_int = random.randint(3, 17)
        min_id = comment_replies[random_int].pk
        max_id = min_id
        count_max = 2
        count_min = 3

        url = self._get_url(post, post_comment)
        response = self.client.get(url, {
            'min_id': min_id,
            'max_id': max_id,
            'count_max': count_max,
            'count_min': count_min
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [int(reply['id']) for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == (count_max + count_min))
        replies_after_min_id = [id for id in response_ids if id >= min_id]
        replies_before_max_id = [id for id in response_ids if id < max_id]
        self.assertTrue(len(replies_after_min_id) == count_min)
        self.assertTrue(len(replies_before_max_id) == count_max)

    def test_should_retrieve_comment_replies_slice_with_sort_for_min_id_and_max_id(self):
        """
        should retrieve comment replies slice sorted ascending for post comments taking into account min_id and max_id
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_replies = 20
        comment_replies = []

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        for i in range(amount_of_replies):
            post_comment_reply = user.reply_to_comment_with_id(post_comment_id=post_comment.pk,
                                                                                text=make_fake_post_comment_text())
            comment_replies.append(post_comment_reply)

        random_int = random.randint(3, 17)
        min_id = comment_replies[random_int].pk
        max_id = min_id
        count_max = 2
        count_min = 3

        url = self._get_url(post, post_comment)
        response = self.client.get(url, {
            'min_id': min_id,
            'max_id': max_id,
            'count_max': count_max,
            'count_min': count_min,
            'sort': 'ASC'
        }, **headers)
        parsed_response = json.loads(response.content)
        response_ids = [int(reply['id']) for reply in parsed_response]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(parsed_response) == (count_max + count_min))
        self.assertTrue(sorted(response_ids) == response_ids)
        replies_after_min_id = [id for id in response_ids if id >= min_id]
        replies_before_max_id = [id for id in response_ids if id < max_id]
        self.assertTrue(len(replies_after_min_id) == count_min)
        self.assertTrue(len(replies_before_max_id) == count_max)

    def _get_create_post_comment_request_data(self, reply_comment_text):
        return {
            'text': reply_comment_text
        }

    def _get_url(self, post, post_comment):
        return reverse('post-comment-replies', kwargs={
            'post_uuid': post.uuid,
            'post_comment_id': post_comment.pk
        })
