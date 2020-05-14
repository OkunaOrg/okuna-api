# Create your tests here.
import json
from django.urls import reverse
from faker import Faker
from rest_framework import status
from unittest import mock
from unittest.mock import ANY
from openbook_common.tests.models import OpenbookAPITestCase

import logging
import random

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_private_community, \
    make_moderation_category, get_test_usernames, make_hashtag_name, make_hashtag
from openbook_hashtags.models import Hashtag
from openbook_moderation.models import ModeratedObject
from openbook_notifications.models import PostCommentNotification, PostCommentReplyNotification, \
    PostCommentUserMentionNotification, Notification
from openbook_posts.models import PostComment, PostCommentUserMention, Post

logger = logging.getLogger(__name__)
fake = Faker()


class PostCommentsAPITests(OpenbookAPITestCase):
    """
    PostCommentsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_retrieve_comments_from_public_community_post(self):
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_closed_public_community_post_if_creator(self):
        """
        should be able to retrieve comments for closed posts if creator
        """

        post_creator = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(post_creator)
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_closed_public_community_post_if_administrator(self):
        """
        should be able to retrieve comments for closed posts if administrator
        """

        post_creator = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)
        community = make_community(creator=admin)
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

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
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)
        # now close the post
        post.is_closed = True
        post.save()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_cant_retrieve_comments_from_private_community_post(self):
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_private_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            post_creator.invite_user_with_username_to_community_with_name(username=commenter.username,
                                                                          community_name=community.name)
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_comments_from_private_community_part_of_post(self):
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        community = make_private_community(creator=post_creator)
        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            post_creator.invite_user_with_username_to_community_with_name(username=commenter.username,
                                                                          community_name=community.name)
            commenter.join_community_with_name(community_name=community.name)
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_public_post(self):
        """
         should be able to retrieve the comments from an own public post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_own_public_post(self):
        """
         should be able to retrieve the comments from an own public post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_own_encircled_post(self):
        """
         should be able to retrieve the comments from an own encircled post and return 200
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        circle = make_circle(creator=user)
        post = user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.connect_with_user_with_id(user.pk)
            user.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_can_retrieve_comments_from_encircled_post_part_of(self):
        """
         should be able to retrieve the comments from an encircled post part of and return 200
         """
        post_creator = make_user()
        circle = make_circle(creator=post_creator)
        user = make_user()

        user.connect_with_user_with_id(post_creator.pk)
        post_creator.confirm_connection_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])

        post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_comments = 5
        comments_ids = []

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.connect_with_user_with_id(post_creator.pk)
            post_creator.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])
            post_comment = commenter.comment_post(post=post, text=make_fake_post_text())
            comments_ids.append(post_comment.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), amount_of_comments)

        for response_comment in response_comments:
            response_comment_id = response_comment.get('id')
            self.assertIn(response_comment_id, comments_ids)

    def test_cannot_retrieve_comments_from_encircled_post_not_part_of(self):
        """
         should not be able to retrieve the comments from an encircled post not part of and return 200
         """
        post_creator = make_user()
        circle = make_circle(creator=post_creator)
        user = make_user()

        post = post_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        amount_of_comments = 5

        for i in range(0, amount_of_comments):
            commenter = make_user()
            commenter.connect_with_user_with_id(post_creator.pk)
            post_creator.confirm_connection_with_user_with_id(user_id=commenter.pk, circles_ids=[circle.pk])

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_comments_from_blocked_user(self):
        """
         should not be able to retrieve the comments from a blocked user
         """
        user = make_user()

        post_creator = make_user()
        blocked_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), 0)

    def test_cannot_retrieve_comments_from_blocking_user(self):
        """
         should not be able to retrieve the comments from a blocking user
         """
        user = make_user()

        post_creator = make_user()
        blocking_user = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())

        blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), 0)

    def test_cannot_retrieve_comments_from_blocked_user_in_a_community(self):
        """
         should not be able to retrieve the comments from a blocked user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocked_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), 0)

    def test_cannot_retrieve_comments_from_blocking_user_in_a_community(self):
        """
         should not be able to retrieve the comments from a blocking user in a community
         """
        user = make_user()

        post_creator = make_user()
        community = make_community(creator=post_creator)

        blocking_user = make_user()

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(len(response_comments), 0)

    def test_can_retrieve_comments_from_blocked_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the comments from a blocked user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocked_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(1, len(response_comments))

        self.assertEqual(response_comments[0]['id'], post_comment.pk)

    def test_can_retrieve_comments_from_blocking_user_in_a_community_if_staff(self):
        """
         should be able to retrieve the comments from a blocking user in a community if staff member
         """
        user = make_user()
        community = make_community(creator=user)
        post_creator = make_user()
        blocking_user = make_user()

        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment = blocking_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        blocking_user.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_comments = json.loads(response.content)

        self.assertEqual(1, len(response_comments))

        self.assertEqual(response_comments[0]['id'], post_comment.pk)

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

    def test_commenting_detects_mentions(self):
        """
        should be able to comment with a mention and detect it once
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_usernames = get_test_usernames()

        post = user.create_public_post(text=make_fake_post_text())

        for test_username in test_usernames:
            test_user = make_user(username=test_username)
            post_text = 'Hello @' + test_user.username + ' @' + test_user.username

            data = {
                'text': post_text
            }

            url = self._get_url(post=post)

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            post_comment = PostComment.objects.get(text=post_text, commenter_id=user.pk)

            self.assertEqual(
                PostCommentUserMention.objects.filter(user_id=test_user.pk, post_comment_id=post_comment.pk).count(), 1)

    def test_commenting_detect_mention_is_case_insensitive(self):
        """
        should detect post comment mentions regardless of the username letter cases
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        mentioned_user = make_user(username='shantanoodles')
        post_comment_text = 'Hello @ShAnTaNoOdLes'

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post=post)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(
            PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk, user_id=mentioned_user.pk).count(),
            1)

    def test_commenting_detect_mention_ignores_username_case(self):
        """
        should detect post comment mentions ignoring the username casing
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        mentioned_user = make_user(username='Shantanoodles')
        post_comment_text = 'Hello @shantanoodles'

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post=post)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(
            PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk, user_id=mentioned_user.pk).count(),
            1)

    def test_create_text_post_comment_ignores_non_existing_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames when creating a post comment
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        fake_username = 'nonexistinguser'
        post_comment_text = 'Hello @' + fake_username

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post=post)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk).count(), 0)

    def test_create_text_post_comment_ignores_comment_creator_username_mention(self):
        """
        should ignore the comment creator username mention when creating a post comment
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = 'Hello @' + user.username

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post=post)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk).count(), 0)

    def test_create_text_post_comment_ignores_if_username_already_commented(self):
        """
        should ignore a username if the person already commented
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())
        mentioned_user = make_user()

        mentioned_user.comment_post(post=post, text=make_fake_post_comment_text())

        post_comment_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_comment_text
        }
        url = self._get_url(post=post)
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        self.assertEqual(PostCommentUserMention.objects.filter(post_comment_id=post_comment.pk).count(), 0)

    def test_create_text_post_comment_creates_mention_notifications(self):
        """
        should be able to create a text post comment with a mention notification
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_user = make_user()
        post_comment_text = 'Hello @' + test_user.username

        post = user.create_public_post(text=make_fake_post_text())

        data = {
            'text': post_comment_text
        }

        url = self._get_url(post=post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)

        post_comment_user_mention = PostCommentUserMention.objects.get(user_id=test_user.pk,
                                                                       post_comment_id=post_comment.pk)

        self.assertEqual(
            PostCommentUserMentionNotification.objects.filter(post_comment_user_mention_id=post_comment_user_mention.pk,
                                                              notification__owner_id=test_user.pk,
                                                              notification__notification_type=Notification.POST_COMMENT_USER_MENTION).count(),
            1)

    def test_create_text_post_comment_with_hashtag_creates_hashtag_if_not_exist(self):
        """
        when creating a post comment with a hashtag, should create it if not exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag_name()

        post_comment_text = 'A hashtag #' + hashtag

        post = user.create_public_post(text=make_fake_post_text())

        data = {
            'text': post_comment_text
        }

        url = self._get_url(post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)
        created_hashtag = Hashtag.objects.get(name=hashtag)
        self.assertTrue(post_comment.hashtags.filter(pk=created_hashtag.pk).exists())
        self.assertEqual(post_comment.hashtags.all().count(), 1)

    def test_create_text_post_comment_with_existing_hashtag_adds_it(self):
        """
        when creating a post commentwith an existing hashtag, should add it
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()

        new_post_comment_text = 'A hashtag #' + hashtag.name

        data = {
            'text': new_post_comment_text
        }

        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post_comment = PostComment.objects.get(text=new_post_comment_text, commenter_id=user.pk)
        self.assertTrue(post_comment.hashtags.filter(pk=hashtag.pk).exists())
        self.assertEqual(Hashtag.objects.filter(pk=hashtag.pk).count(), 1)
        self.assertEqual(post_comment.hashtags.all().count(), 1)

    def test_create_text_post_comment_with_repeated_hashtag_does_not_create_double_hashtags(self):
        """
        when creating a post commentwith a repeated hashtag, doesnt create it twice
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag_name = make_hashtag_name()
        post_comment_text = '#%s #%s' % (hashtag_name, hashtag_name)

        data = {
            'text': post_comment_text
        }

        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=user.pk)
        hashtag = Hashtag.objects.get(name=hashtag_name)
        self.assertEqual(post_comment.hashtags.all().count(), 1)
        self.assertEqual(post_comment.hashtags.filter(name=hashtag.name).count(), 1)
        self.assertEqual(Hashtag.objects.filter(name=hashtag.name).count(), 1)

    def test_commenting_in_a_post_sets_language_for_comment(self):
        """
         should set comment language when user comments in a post and return 201
         """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_comment = PostComment.objects.get(post_id=post.pk, text=post_comment_text)
        self.assertTrue(post_comment.language is not None)

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

    def test_cannot_comment_in_blocked_user_post(self):
        """
          should not be able to comment in a blocked user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_cannot_comment_in_blocking_user_post(self):
        """
          should not be able to comment in a blocking user post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        user_to_block = make_user()

        user.follow_user_with_id(user_to_block.pk)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_cannot_comment_in_blocked_user_community_post(self):
        """
          should not be able to comment in a blocked user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_cannot_comment_in_blocking_user_community_post(self):
        """
          should not be able to comment in a blocking user community post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_can_comment_in_blocked_community_staff_member_post(self):
        """
          should be able to comment in a blocked community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).count() == 1)

    def test_can_comment_in_blocking_community_staff_member_post(self):
        """
          should be able to comment in a blocking community staff member post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).count() == 1)

    def test_owner_cannot_comment_in_community_post_with_disabled_comments(self):
        """
         should not be able to comment in the community post with comments disabled even if owner of post
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_foreign_user_cannot_comment_in_community_post_with_disabled_comments(self):
        """
         should not be able to comment in the community post with comments disabled even if foreign user
         """
        user = make_user()
        foreign_user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(foreign_user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_administrator_can_comment_in_community_post_with_disabled_comments(self):
        """
         should be able to comment in the community post with comments disabled if administrator
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment = PostComment.objects.get(post_id=post.pk, text=post_comment_text, commenter=admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())
        self.assertEqual(response_id, post_comment.id)

    def test_moderator_can_comment_in_community_post_with_disabled_comments(self):
        """
         should be able to comment in the community post with comments disabled if moderator
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
        post.comments_enabled = False
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment = PostComment.objects.get(post_id=post.pk, text=post_comment_text, commenter=moderator)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())
        self.assertEqual(response_id, post_comment.id)

    def test_owner_can_comment_on_closed_community_post(self):
        """
         should be able to comment in the community post which is closed
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_foreign_user_cannot_comment_on_closed_community_post(self):
        """
         should not be able to comment in the community post that is closed
         """
        user = make_user()
        foreign_user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(foreign_user)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())

    def test_moderator_can_comment_on_closed_community_post(self):
        """
         should be able to comment on the community post which is closed if moderator
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
        post.comments_enabled = False
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment = PostComment.objects.get(post_id=post.pk, text=post_comment_text, commenter=moderator)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())
        self.assertEqual(response_id, post_comment.id)

    def test_administrator_can_comment_on_closed_community_post(self):
        """
         should be able to comment in the community post which is closed if administrator
         """
        user = make_user()
        admin = make_user()
        headers = make_authentication_headers_for_user(admin)

        community = make_community(admin)
        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()
        post_comment_text = make_fake_post_comment_text()
        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        response_id = parsed_response['id']
        post_comment = PostComment.objects.get(post_id=post.pk, text=post_comment_text, commenter=admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=post_comment_text).exists())
        self.assertEqual(response_id, post_comment.id)

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

    def test_cannot_comment_in_post_from_community_banned_from(self):
        """
          should not be able to comment in the post of a community banned from and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        user.comment_post(post=post, text=make_fake_post_comment_text())

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        new_post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(new_post_comment_text)

        url = self._get_url(post)
        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PostComment.objects.filter(post_id=post.pk, text=new_post_comment_text).count() == 0)

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

        self.assertEqual(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=foreign_user).count(), 1)

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

    def test_commenting_in_post_does_not_create_notification_if_user_is_blocked(self):
        """
         should not create a notification when a blocked user comments on a post
         """
        foreign_user = make_user()
        user = make_user()
        blocked_user = make_user()
        headers = make_authentication_headers_for_user(blocked_user)
        post = foreign_user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.block_user_with_username(blocked_user.username)
        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=user).exists())

    @mock.patch('openbook_notifications.helpers.send_post_comment_push_notification_with_message')
    def test_commenting_in_post_does_not_send_push_notification_if_user_is_blocked(self,
                                                                                   send_post_comment_push_notification_call):
        """
         should NOT send a push notification when a blocked user comments on a post
         """
        foreign_user = make_user()
        user = make_user()
        blocked_user = make_user()
        headers = make_authentication_headers_for_user(blocked_user)
        post = foreign_user.create_public_post(text=make_fake_post_text())
        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.block_user_with_username(blocked_user.username)
        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)
        send_post_comment_push_notification_call.reset_mock()

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        post_comment = PostComment.objects.get(text=post_comment_text, commenter_id=blocked_user.pk)

        # assert notification only for the post creator, not user who blocked the commenting user
        send_post_comment_push_notification_call.assert_called_once()
        send_post_comment_push_notification_call.assert_called_with(
            post_comment=post_comment,
            message=ANY,
            target_user=foreign_user
        )

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

        self.assertEqual(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=foreign_user).count(), 1)

    def test_commenting_in_commented_post_by_foreign_user_creates_foreign_notification_when_muted(self):
        """
         should create a notification when a user comments in a post where a foreign user commented and muted before
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

        self.assertEqual(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=foreign_user).count(), 1)

    def test_comment_in_an_encircled_post_with_a_user_removed_from_the_circle_not_notifies_it(self):
        """
         should not create a comment notification for a user that has been been removed from an encircled post circle
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

        # Comment so we "subscribe" for notifications
        foreign_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_text())

        # Remove him from the circles
        post_owner.update_connection_with_user_with_id(user_id=foreign_user.pk,
                                                       circles_ids=[post_owner.connections_circle_id])

        post_comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(post_comment_text)

        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentNotification.objects.filter(post_comment__text=post_comment_text,
                                                                notification__owner=foreign_user).exists())

    def test_foreign_comment_should_not_create_notification_if_user_has_only_replied_to_a_comment(self):
        """
         should NOT get notification when a foreign user comments directly on a post where the current user
         has replied to one of the comments
         """
        user = make_user()
        foreign_user = make_user()
        headers = make_authentication_headers_for_user(foreign_user)

        post_creator = make_user()

        post = post_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_creator.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())
        user.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk, post_uuid=post.uuid,
                                                         text=make_fake_post_comment_text())

        comment_text = make_fake_post_comment_text()

        data = self._get_create_post_comment_request_data(comment_text)
        # foreign user comments
        url = self._get_url(post)
        self.client.put(url, data, **headers)

        self.assertFalse(PostCommentReplyNotification.objects.filter(post_comment__text=comment_text,
                                                                     notification__owner=user).exists())

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

    def test_cannot_retrieve_comments_of_own_soft_deleted_post(self):
        """
        should not be able to retrieve the comments of a soft deleted post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            user.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post.soft_delete()

        url = self._get_url(post)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cannot_retrieve_comments_of_foreign_soft_deleted_post(self):
        """
        should not be able to retrieve the comments of a soft deleted post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        amount_of_post_comments = 10

        for i in range(amount_of_post_comments):
            post_comment_text = make_fake_post_comment_text()
            user.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post.soft_delete()

        url = self._get_url(post)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_reported_connected_user_post_comments(self):
        """
        should not be able to retrieve reported connected user post comments
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_comment_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_comment_circle.pk])
        connected_user_post = connected_user.create_encircled_post(text=make_fake_post_comment_text(),
                                                                   circles_ids=[connected_user_post_comment_circle.pk])

        post_comment = connected_user.comment_post(post=connected_user_post, text=make_fake_post_text())

        user.report_comment_for_post(post=connected_user_post, post_comment=post_comment,
                                     category_id=make_moderation_category().pk)

        url = self._get_url(post=connected_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comment_comments = json.loads(response.content)

        self.assertEqual(0, len(response_post_comment_comments))

    def test_cant_retrieve_reported_following_user_post_comments(self):
        """
        should not be able to retrieve reported following user post comments
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_comment_text())
        post_comment = following_user.comment_post(post=following_user_post, text=make_fake_post_text())

        user.report_comment_for_post(post=following_user_post, post_comment=post_comment,
                                     category_id=make_moderation_category().pk)

        url = self._get_url(post=following_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comment_comments = json.loads(response.content)

        self.assertEqual(0, len(response_post_comment_comments))

    def test_cant_retrieve_reported_community_post_comments(self):
        """
        should not be able to retrieve reported community post comments
        """
        user = make_user()

        community = make_community()

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_comment_text())

        post_comment = post_creator.comment_post(post=post, text=make_fake_post_text())

        user.report_comment_for_post(post=post, post_comment=post_comment,
                                     category_id=make_moderation_category().pk)

        url = self._get_url(post=post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comment_comments = json.loads(response.content)

        self.assertEqual(0, len(response_post_comment_comments))

    def test_cant_retrieve_moderated_approved_community_post_comments(self):
        """
        should not be able to retrieve moderated approved community post comments
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_comment_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_comment_creator.join_community_with_name(community_name=community.name)

        number_of_post_comments = 5
        post_reporter = make_user()
        report_category = make_moderation_category()

        post = post_comment_creator.create_community_post(community_name=community.name,
                                                          text=make_fake_post_comment_text())

        for i in range(0, number_of_post_comments):
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_text())
            post_reporter.report_comment_for_post(post=post, post_comment=post_comment,
                                                  category_id=make_moderation_category().pk)
            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
                post_comment=post_comment,
                category_id=report_category.pk)
            community_creator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comments = json.loads(response.content)

        self.assertEqual(0, len(response_post_comments))

    def test_can_retrieve_moderated_rejected_community_post_comments(self):
        """
        should not be able to retrieve moderated rejected community post comments
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_comment_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_comment_creator.join_community_with_name(community_name=community.name)

        number_of_post_comments = 5
        post_reporter = make_user()
        report_category = make_moderation_category()
        post_comments_ids = []
        post = post_comment_creator.create_community_post(community_name=community.name,
                                                          text=make_fake_post_comment_text())
        for i in range(0, number_of_post_comments):
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_text())
            post_comments_ids.append(post_comment.pk)
            post_reporter.report_comment_for_post(post=post, post_comment=post_comment,
                                                  category_id=make_moderation_category().pk)
            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
                post_comment=post_comment,
                category_id=report_category.pk)
            community_creator.reject_moderated_object(moderated_object=moderated_object)

        headers = make_authentication_headers_for_user(user)
        url = self._get_url(post=post)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comments = json.loads(response.content)

        self.assertEqual(len(post_comments_ids), len(response_post_comments))

        response_post_comments_ids = [post_comment['id'] for post_comment in response_post_comments]

        for post_id in post_comments_ids:
            self.assertIn(post_id, response_post_comments_ids)

    def test_can_retrieve_moderated_pending_community_post_comments(self):
        """
        should not be able to retrieve moderated pending community post comments
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_comment_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_comment_creator.join_community_with_name(community_name=community.name)

        number_of_post_comments = 5
        post_reporter = make_user()
        post_comments_ids = []
        post = post_comment_creator.create_community_post(community_name=community.name,
                                                          text=make_fake_post_comment_text())
        for i in range(0, number_of_post_comments):
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_text())
            post_comments_ids.append(post_comment.pk)
            post_reporter.report_comment_for_post(post=post, post_comment=post_comment,
                                                  category_id=make_moderation_category().pk)

        headers = make_authentication_headers_for_user(user)
        url = self._get_url(post=post)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post_comments = json.loads(response.content)

        self.assertEqual(len(post_comments_ids), len(response_post_comments))

        response_post_comments_ids = [post_comment['id'] for post_comment in response_post_comments]

        for post_id in post_comments_ids:
            self.assertIn(post_id, response_post_comments_ids)

    def _get_create_post_comment_request_data(self, post_comment_text):
        return {
            'text': post_comment_text
        }

    def _get_url(self, post):
        return reverse('post-comments', kwargs={
            'post_uuid': post.uuid,
        })


class PostCommentsEnableAPITests(OpenbookAPITestCase):
    """
    PostCommentsEnable APITests
    """

    def test_can_enable_comments_on_post_if_moderator_of_community(self):
        """
         should be able to enable comments if moderator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.comments_enabled)
        self.assertTrue(parsed_response['comments_enabled'])

    def test_can_enable_comments_on_post_if_administrator_of_community(self):
        """
         should be able to enable comments if administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.comments_enabled)
        self.assertTrue(parsed_response['comments_enabled'])

    def test_logs_enabled_comments_on_post_by_administrator_of_community(self):
        """
         should log enable comments by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='EPC',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def test_cannot_enable_comments_on_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to enable comments if not administrator/moderator
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.comments_enabled = False
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertFalse(post.comments_enabled)

    def _get_url(self, post):
        return reverse('enable-post-comments', kwargs={
            'post_uuid': post.uuid
        })


class PostCommentsDisableAPITests(OpenbookAPITestCase):
    """
    PostCommentsDisable APITests
    """

    def test_can_disable_comments_on_post_if_moderator_of_community(self):
        """
         should be able to disable comments if moderator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.comments_enabled)
        self.assertFalse(parsed_response['comments_enabled'])

    def test_can_disable_comments_on_post_if_administrator_of_community(self):
        """
         should be able to disable comments if administrator of a community
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
        self.assertFalse(post.comments_enabled)
        self.assertFalse(parsed_response['comments_enabled'])

    def test_logs_disabled_comments_on_post_by_administrator_of_community(self):
        """
         should log disable comments by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='DPC',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def test_cannot_disable_comments_on_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to disable comments if not administrator/moderator
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
        self.assertTrue(post.comments_enabled)

    def _get_url(self, post):
        return reverse('disable-post-comments', kwargs={
            'post_uuid': post.uuid
        })
