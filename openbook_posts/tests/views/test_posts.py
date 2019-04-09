# Create your tests here.
import tempfile

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from mixer.backend.django import mixer

from openbook.settings import POST_MAX_LENGTH
from openbook_auth.models import User
import random

import logging
import json

from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_users, make_fake_post_text, \
    make_authentication_headers_for_user, make_circle, make_community
from openbook_lists.models import List

logger = logging.getLogger(__name__)
fake = Faker()


# TODO A lot of setup duplication. Perhaps its a good idea to create a single factory on top of mixer or Factory boy


class PostsAPITests(APITestCase):
    """
    PostsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_create_text_post(self):
        """
        should be able to create a text post and return 201
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

        world_circle = Circle.get_world_circle()

        self.assertTrue(world_circle.posts.filter(text=post_text).count() == 1)

    def test_create_post_is_added_to_world_circle(self):
        """
        the created text post should automatically added to world circle
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'text': post_text
        }

        url = self._get_url()

        self.client.put(url, data, **headers, format='multipart')

        world_circle = Circle.get_world_circle()

        self.assertTrue(world_circle.posts.filter(text=post_text).count() == 1)

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

    def test_cannot_create_post_in_foreign_circle(self):
        """
        should NOT be able to create a text post in an foreign circle and return 400
        """
        user = make_user()
        foreign_user = make_user()

        circle = mixer.blend(Circle, creator=foreign_user)

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.posts.filter(text=post_text).count() == 0)

        self.assertTrue(circle.posts.filter(text=post_text).count() == 0)

    def test_can_create_post_in_world_circle(self):
        """
        should be able to create a post in the world circle and return 201
        """
        user = make_user()

        circle = Circle.get_world_circle()

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.filter(text=post_text).exists())

        self.assertTrue(circle.posts.filter(text=post_text).exists())

    def test_create_image_post(self):
        """
        should be able to create an image post and return 201
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'image': tmp_file
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertTrue(user.posts.count() == 1)

        created_post = user.posts.filter(pk=response_post_id).get()

        self.assertTrue(hasattr(created_post, 'image'))

    def test_create_image_and_text_post(self):
        """
        should be able to create an image and text post and return 201
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

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertTrue(user.posts.count() == 1)

        created_post = user.posts.filter(pk=response_post_id).get()

        self.assertEqual(created_post.text, post_text)

        self.assertTrue(hasattr(created_post, 'image'))

    def test_create_video_post(self):
        """
        should be able to create a video post and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        video = SimpleUploadedFile("file.mp4", b"video_file_content", content_type="video/mp4")

        data = {
            'video': video
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertTrue(user.posts.count() == 1)

        created_post = user.posts.filter(pk=response_post_id).get()

        self.assertTrue(hasattr(created_post, 'video'))

    def test_create_video_and_text_post(self):
        """
        should be able to create a video and text post and return 201
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        video = SimpleUploadedFile("file.mp4", b"video_file_content", content_type="video/mp4")

        data = {
            'text': post_text,
            'video': video
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertTrue(user.posts.count() == 1)

        created_post = user.posts.filter(pk=response_post_id).get()

        self.assertEqual(created_post.text, post_text)

        self.assertTrue(hasattr(created_post, 'video'))

    def test_cannot_create_both_video_and_image_post(self):
        """
        should not be able to create both a video and image
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        video = SimpleUploadedFile("file.mp4", b"video_file_content", content_type="video/mp4")
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'image': tmp_file,
            'video': video
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_posts(self):
        """
        should be able to retrieve all posts
        """

        # BEWARE The max count for the API is 20. If we are checking for more than 20
        # posts, it will fail

        user = mixer.blend(User)
        auth_token = user.auth_token.key

        amount_of_own_posts = 5

        user_posts_ids = []
        for i in range(amount_of_own_posts):
            post = user.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            user_posts_ids.append(post.pk)

        amount_of_users_to_follow = 5

        lists_to_follow_in = mixer.cycle(amount_of_users_to_follow).blend(List, creator=user)

        users_to_follow = mixer.cycle(amount_of_users_to_follow).blend(User)
        users_to_follow_posts_ids = []

        for index, user_to_follow in enumerate(users_to_follow):
            user.follow_user(user_to_follow, lists_ids=[lists_to_follow_in[index].pk])
            post = user_to_follow.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_follow_posts_ids.append(post.pk)

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)
        users_to_connect_posts_ids = []

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circles_to_connect_in[index].pk])
            post = user_to_connect.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_connect_posts_ids.append(post.pk)

        amount_of_community_posts = 5
        community_posts_ids = []

        for i in range(0, amount_of_community_posts):
            community_creator = make_user()
            community = make_community(creator=community_creator, type='P')
            user.join_community_with_name(community_name=community.name)
            community_member = make_user()
            community_member.join_community_with_name(community_name=community.name)
            community_post = community_member.create_community_post(text=make_fake_post_text(),
                                                                    community_name=community.name)
            community_posts_ids.append(community_post.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        all_posts_ids = users_to_connect_posts_ids + users_to_follow_posts_ids + user_posts_ids + community_posts_ids

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
            user.follow_user(user_to_follow, lists_ids=[lists_to_follow_in[index].pk])
            user_to_follow.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circles_to_connect_in[index].pk])
            user_to_connect.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        number_of_circles_to_retrieve_posts_from = 3

        circles_to_retrieve_posts_from = mixer.cycle(number_of_circles_to_retrieve_posts_from).blend(Circle,
                                                                                                     creator=user)

        in_circle_posts_ids = []

        for index, circle_to_retrieve_posts_from in enumerate(circles_to_retrieve_posts_from):
            user_in_circle = mixer.blend(User)
            user.connect_with_user_with_id(user_in_circle.pk, circles_ids=[circle_to_retrieve_posts_from.pk])
            post_in_circle = user_in_circle.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            in_circle_posts_ids.append(post_in_circle.pk)

        number_of_expected_posts = number_of_circles_to_retrieve_posts_from

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        url = self._get_url()

        circles_query_str_value = ','.join(map(str, [circle.pk for circle in circles_to_retrieve_posts_from]))

        response = self.client.get(url, {'circle_id': circles_query_str_value}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), number_of_expected_posts)

        for response_post in response_posts:
            self.assertIn(response_post.get('id'), in_circle_posts_ids)

    def test_get_all_lists_posts(self):
        """
        should be able to retrieve all posts for a given list
        """

        user = mixer.blend(User)
        auth_token = user.auth_token.key

        amount_of_users_to_follow = 5

        lists_to_follow_in = mixer.cycle(amount_of_users_to_follow).blend(List, creator=user)

        users_to_follow = mixer.cycle(amount_of_users_to_follow).blend(User)

        for index, user_to_follow in enumerate(users_to_follow):
            user.follow_user(user_to_follow, lists_ids=[lists_to_follow_in[index].pk])
            user_to_follow.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circles_to_connect_in[index].pk])
            user_to_connect.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))

        number_of_lists_to_retrieve_posts_from = 3

        lists_to_retrieve_posts_from = mixer.cycle(number_of_lists_to_retrieve_posts_from).blend(List,
                                                                                                 creator=user)
        in_list_posts_ids = []

        for index, list_to_retrieve_posts_from in enumerate(lists_to_retrieve_posts_from):
            user_in_list = mixer.blend(User)
            user.follow_user(user_in_list, lists_ids=[list_to_retrieve_posts_from.pk])
            post_in_list = user_in_list.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            in_list_posts_ids.append(post_in_list.pk)

        number_of_expected_posts = number_of_lists_to_retrieve_posts_from

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        url = self._get_url()

        lists_query_str_value = ','.join(map(str, [list.pk for list in lists_to_retrieve_posts_from]))

        response = self.client.get(url, {'list_id': lists_query_str_value}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(number_of_expected_posts, len(response_posts))

        for response_post in response_posts:
            self.assertIn(response_post.get('id'), in_list_posts_ids)

    def test_get_all_posts_with_max_id_and_count(self):
        """
        should be able to retrieve all posts with a max id and count
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        amount_of_own_posts = 10

        user_posts_ids = []
        for i in range(amount_of_own_posts):
            post = user.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            user_posts_ids.append(post.pk)

        amount_of_users_to_follow = 5

        lists_to_follow_in = mixer.cycle(amount_of_users_to_follow).blend(List, creator=user)

        users_to_follow = mixer.cycle(amount_of_users_to_follow).blend(User)
        users_to_follow_posts_ids = []

        for index, user_to_follow in enumerate(users_to_follow):
            user.follow_user(user_to_follow, lists_ids=[lists_to_follow_in[index].pk])
            post = user_to_follow.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_follow_posts_ids.append(post.pk)

        amount_of_users_to_connect = 5

        circles_to_connect_in = mixer.cycle(amount_of_users_to_connect).blend(Circle, creator=user)

        users_to_connect = mixer.cycle(amount_of_users_to_connect).blend(User)
        users_to_connect_posts_ids = []

        for index, user_to_connect in enumerate(users_to_connect):
            user.connect_with_user_with_id(user_to_connect.pk, circles_ids=[circles_to_connect_in[index].pk])
            post = user_to_connect.create_public_post(text=fake.text(max_nb_chars=POST_MAX_LENGTH))
            users_to_connect_posts_ids.append(post.pk)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        all_posts_ids = users_to_connect_posts_ids + users_to_follow_posts_ids + user_posts_ids

        url = self._get_url()

        max_id = 10

        count = 3

        response = self.client.get(url, {
            'count': count,
            'max_id': max_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(count, len(response_posts))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, all_posts_ids)
            self.assertTrue(response_post_id < max_id)

    def test_get_all_public_posts_for_unconnected_user(self):
        """
        should be able to retrieve all the public posts of an unconnected user
        and return 200
        """
        user = make_user()

        amount_of_users_to_follow = random.randint(1, 5)

        users_to_retrieve_posts_from = make_users(amount_of_users_to_follow)

        for user_to_retrieve_posts_from in users_to_retrieve_posts_from:
            post_text = make_fake_post_text()
            user_to_retrieve_posts_from.create_public_post(text=post_text)

        user_to_retrieve_posts_from = random.choice(users_to_retrieve_posts_from)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user_to_retrieve_posts_from.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 1)

        post = response_posts[0]

        self.assertEqual(post['creator']['id'], user_to_retrieve_posts_from.pk)

    def test_get_all_public_posts_for_connected_user(self):
        """
        should be able to retrieve all the posts of a connected user
        and return 200
        """
        user = make_user()

        user_to_connect_with = make_user()

        user.connect_with_user_with_id(user_to_connect_with.pk)
        user_to_connect_with.confirm_connection_with_user_with_id(user.pk)

        amount_of_public_posts = random.randint(1, 5)
        amount_of_encircled_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_public_posts):
            post = user_to_connect_with.create_public_post(make_fake_post_text())
            created_posts_ids.append(post.pk)

        circle = make_circle(creator=user_to_connect_with)

        user_to_connect_with.update_connection_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])

        for i in range(amount_of_encircled_posts):
            post = user_to_connect_with.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user_to_connect_with.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(created_posts_ids))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_get_all_public_posts_for_user_unauthenticated(self):
        """
        should be able to retrieve all the public posts of an specific user
        being unauthenticated and return 200
        """
        user = make_user()

        amount_of_user_public_posts = random.randint(1, 5)
        amount_of_user_encircled_posts = random.randint(1, 5)

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        for i in range(amount_of_user_encircled_posts):
            post_text = make_fake_post_text()
            circle = make_circle(creator=user)
            user.create_encircled_post(text=post_text, circles_ids=[circle.pk])

        url = self._get_url()

        response = self.client.get(url, {
            'username': user.username
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(public_posts_ids))

        response_posts_ids = [response_post['id'] for response_post in response_posts]

        for public_post_id in public_posts_ids:
            self.assertIn(public_post_id, response_posts_ids)

    def test_get_all_own_posts(self):
        """
        should be able to retrieve all own posts
        and return 200
        """
        user = make_user()

        amount_of_public_posts = random.randint(1, 5)
        amount_of_encircled_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_public_posts):
            post = user.create_public_post(make_fake_post_text())
            created_posts_ids.append(post.pk)

        circle = make_circle(creator=user)

        for i in range(amount_of_encircled_posts):
            post = user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(created_posts_ids))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_filter_community_post_from_own_posts(self):
        """
        should filter out the community posts when retrieving all own posts and return 200
        """
        user = make_user()
        community = make_community(creator=user)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_get_all_public_posts_for_user_unauthenticated_with_max_id_and_count(self):
        """
        should be able to retrieve all the public posts of an specific user
        using max_id and count being unauthenticated and return 200
        """
        user = make_user()

        amount_of_user_public_posts = 10

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        count = 5

        max_id = 6

        response = self.client.get(url, {
            'username': user.username,
            'count': count,
            'max_id': max_id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), count)

        response_posts_ids = [response_post['id'] for response_post in response_posts]

        for response_post_id in response_posts_ids:
            self.assertTrue(response_post_id < max_id)

    def test_retrieves_no_posts_when_filtering_on_empty_circle(self):
        """
        should retrieve no posts when filtering on an empty circle
        """
        user = make_user()
        connections_circle_id = user.connections_circle_id

        headers = make_authentication_headers_for_user(user)

        amount_of_foreign_public_posts = 10

        public_posts_ids = []

        for i in range(amount_of_foreign_public_posts):
            post_text = make_fake_post_text()
            foreign_user = make_user()
            public_post = foreign_user.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        response = self.client.get(url, {'circle_id': connections_circle_id}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_retrieves_own_posts_of_own_filtered_circle(self):
        """
        should retrieve own posts when filtering on a circle that is from us
        """
        user = make_user()

        circle = make_circle(creator=user)
        circle_id = circle.pk

        headers = make_authentication_headers_for_user(user)

        amount_of_posts = 10

        posts_ids = []

        for i in range(amount_of_posts):
            post_text = make_fake_post_text()
            post = user.create_encircled_post(text=post_text, circles_ids=[circle_id])
            posts_ids.append(post.pk)

        url = self._get_url()

        response = self.client.get(url, {'circle_id': circle_id}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_posts))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_can_retrieve_encircled_posts_of_confirmed_connection(self):
        """
        should be able to retrieve the encircled posts of a confirmed connection
        """
        user = make_user()
        user_to_connect_to = make_user()

        user.connect_with_user_with_id(user_id=user_to_connect_to.pk)

        user_to_connect_to_circle = make_circle(creator=user_to_connect_to)
        user_to_connect_to.confirm_connection_with_user_with_id(user_id=user.pk,
                                                                circles_ids=[user_to_connect_to_circle.pk])

        post = user_to_connect_to.create_encircled_post(text=make_fake_post_text(),
                                                        circles_ids=[user_to_connect_to_circle.pk])

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_encircled_posts_of_unconfirmed_connection(self):
        """
        should not be able to retrieve encircled posts of unconfirmed co
        """
        user = make_user()
        user_to_connect_to = make_user()

        user.connect_with_user_with_id(user_id=user_to_connect_to.pk)

        user_to_connect_to_circle = make_circle(creator=user_to_connect_to)

        user_to_connect_to.create_encircled_post(text=make_fake_post_text(),
                                                 circles_ids=[user_to_connect_to_circle.pk])

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_can_retrieve_posts_with_recent_unconfirmed_connection_encircled_post(self):
        """
        should be able to retrieve the timeline posts with an unconfirmed connection recent posts
        https://github.com/OpenbookOrg/openbook-api/issues/301
        """
        user = make_user()

        user_timeline_posts_amount = 5

        posts_ids = []

        for i in range(0, user_timeline_posts_amount):
            foreign_user = make_user()
            foreign_post = foreign_user.create_encircled_post(text=make_fake_post_text(),
                                                              circles_ids=[foreign_user.connections_circle_id])
            posts_ids.append(foreign_post.pk)
            user.connect_with_user_with_id(user_id=foreign_user.pk)
            foreign_user.confirm_connection_with_user_with_id(user_id=user.pk)

        connection_requester_user = make_user()

        connection_requester_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[
            connection_requester_user.connections_circle.pk])

        user.confirm_connection_with_user_with_id(user_id=connection_requester_user.pk)

        connection_requester_user.disconnect_from_user_with_id(user_id=user.pk)

        connection_requester_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[
            connection_requester_user.connections_circle.pk])

        connection_requester_user_circle = make_circle(creator=connection_requester_user)
        connection_requester_user.update_connection_with_user_with_id(user_id=user.pk,
                                                                      circles_ids=[connection_requester_user_circle.pk])

        connection_requester_user.create_encircled_post(text=make_fake_post_text(),
                                                        circles_ids=[connection_requester_user_circle.pk])

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_posts))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def _get_url(self):
        return reverse('posts')
