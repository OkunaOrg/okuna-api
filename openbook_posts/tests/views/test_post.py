# Create your tests here.

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User

import logging
import json

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text
from openbook_posts.models import Post

logger = logging.getLogger(__name__)
fake = Faker()


class PostItemAPITests(APITestCase):
    """
    PostItemAPI
    """

    def test_can_delete_own_post(self):
        user = mixer.blend(User)
        headers = make_authentication_headers_for_user(user)
        post = user.create_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_cannot_delete_foreign_post(self):
        user = mixer.blend(User)
        headers = make_authentication_headers_for_user(user)

        foreign_user = mixer.blend(User)
        post = foreign_user.create_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 1)

    def _get_url(self, post):
        return reverse('post', kwargs={
            'post_id': post.pk
        })


class PostCommentsAPITests(APITestCase):
    """
    PostCommentsAPI
    """

    def test_can_comment_in_own_post(self):
        pass

    def test_cannot_comment_in_foreign_post(self):
        pass

    def test_can_comment_in_connected_user_public_post(self):
        pass

    def test_can_comment_in_connected_user_encircled_post_part_of(self):
        pass

    def test_cannot_comment_in_connected_user_encircled_post_not_part_of(self):
        pass

    def test_can_comment_in_followed_user_public_post(self):
        pass

    def test_cannot_comment_in_followed_user_encircled_post(self):
        pass


class PostCommentItemAPITests(APITestCase):
    """
    PostCommentItemAPI
    """

    def test_can_delete_foreign_comment_in_own_post(self):
        pass

    def test_can_delete_own_comment_in_foreign_post(self):
        pass

    def test_cannot_delete_foreign_comment_in_foreign_post(self):
        pass

    def test_can_delete_own_comment_in_connected_user_public_post(self):
        pass

    def test_cannot_delete_foreign_comment_in_connected_user_public_post(self):
        pass

    def test_cannot_delete_foreign_comment_in_connected_user_encircled_post_part_of(self):
        pass

    def test_cannot_delete_foreign_comment_in_connected_user_encircled_post_not_part_of(self):
        pass

    def test_can_delete_own_comment_in_followed_user_public_post(self):
        pass

    def test_cannot_delete_foreign_comment_in_followed_user_public_post(self):
        pass

    def test_cannot_delete_foreign_comment_in_folowed_user_encircled_post(self):
        pass
