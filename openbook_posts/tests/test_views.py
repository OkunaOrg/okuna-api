# Create your tests here.
import tempfile

from PIL import Image
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook.settings import POST_MAX_LENGTH
from openbook_auth.models import User

import logging
import json

from openbook_circles.models import Circle
from openbook_lists.models import List

logger = logging.getLogger(__name__)
fake = Faker()


class PostsAPITests(APITestCase):
    """
    PostsAPI
    """

    def test_create_post(self):
        """
        should be able to create a text post automatically added to world circle and  return 201
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.filter(text=post_text).count() == 1)

        self.assertTrue(user.world_circle.posts.filter(text=post_text).count() == 1)

    def test_create_image_post(self):
        """
        should be able to create an image post and return 201
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'text': post_text,
            'image': tmp_file
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.filter(text=post_text).count() == 1)

        created_post = user.posts.filter(text=post_text).get()

        self.assertTrue(hasattr(created_post, 'image'))

    def test_get_all_posts(self):
        """
        should be able to retrieve all posts
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        amount_of_users_to_follow = 5

        lists_to_follow_in = mixer.cycle(amount_of_users_to_follow).blend(List, creator=user)

        users_to_follow = mixer.cycle(amount_of_users_to_follow).blend(User)
        users_to_follow_posts_ids = []

        for index, user_to_follow in enumerate(users_to_follow):
            user.follow_user(user_to_follow, list=lists_to_follow_in[index])
            post = user_to_follow.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_follow_posts_ids.append(post.pk)

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)
        users_to_connect_posts_ids = []

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user(user_to_connect, circle=circles_to_connect_in[index])
            post = user_to_connect.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_connect_posts_ids.append(post.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        url = self._get_url()

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        all_posts_ids = users_to_connect_posts_ids + users_to_follow_posts_ids

        self.assertEqual(len(all_posts_ids), len(response_posts))

        for response_post in response_posts:
            self.assertIn(response_post.get('id'), all_posts_ids)

    def _get_url(self):
        return reverse('posts')
