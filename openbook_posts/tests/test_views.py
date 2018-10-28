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
from openbook_posts.models import Post

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

    def test_create_post_in_circle(self):
        """
        should be able to create a text post in an specified circle and  return 201
        """
        user = mixer.blend(User)

        circle = mixer.blend(Circle, creator=user)

        auth_token = user.auth_token.key

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.filter(text=post_text).count() == 1)

        self.assertTrue(circle.posts.filter(text=post_text).count() == 1)

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

        amount_of_own_posts = 5

        user_posts_ids = []
        for i in range(amount_of_own_posts):
            post = user.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            user_posts_ids.append(post.pk)

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

        all_posts_ids = users_to_connect_posts_ids + users_to_follow_posts_ids + user_posts_ids

        url = self._get_url()

        response = self.client.get(url, {'count': len(all_posts_ids)}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(all_posts_ids), len(response_posts))

        for response_post in response_posts:
            self.assertIn(response_post.get('id'), all_posts_ids)

    def test_get_all_circle_posts(self):
        """
        should be able to retrieve all posts for a given circle
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        amount_of_users_to_follow = 5

        lists_to_follow_in = mixer.cycle(amount_of_users_to_follow).blend(List, creator=user)

        users_to_follow = mixer.cycle(amount_of_users_to_follow).blend(User)

        for index, user_to_follow in enumerate(users_to_follow):
            user.follow_user(user_to_follow, list=lists_to_follow_in[index])
            user_to_follow.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user(user_to_connect, circle=circles_to_connect_in[index])
            user_to_connect.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        number_of_circles_to_retrieve_posts_from = 3

        circles_to_retrieve_posts_from = mixer.cycle(number_of_circles_to_retrieve_posts_from).blend(Circle,
                                                                                                     creator=user)

        in_circle_posts_ids = []

        for index, circle_to_retrieve_posts_from in enumerate(circles_to_retrieve_posts_from):
            user_in_circle = mixer.blend(User)
            user.connect_with_user(user_in_circle, circle=circle_to_retrieve_posts_from)
            post_in_circle = user_in_circle.create_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            in_circle_posts_ids.append(post_in_circle.pk)

        number_of_expected_posts = number_of_circles_to_retrieve_posts_from

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        url = self._get_url()

        circles_query_str_value = ','.join(map(str, [circle.pk for circle in circles_to_retrieve_posts_from]))

        response = self.client.get(url, {'circle_id': circles_query_str_value}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(number_of_expected_posts, len(response_posts))

        for response_post in response_posts:
            self.assertIn(response_post.get('id'), in_circle_posts_ids)

    def _get_url(self):
        return reverse('posts')
