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
    make_authentication_headers_for_user, make_circle, make_community, make_list, make_moderation_category, \
    get_test_usernames
from openbook_common.utils.helpers import sha256sum
from openbook_lists.models import List
from openbook_moderation.models import ModeratedObject
from openbook_notifications.models import PostUserMentionNotification, Notification
from openbook_posts.models import Post, PostUserMention

logger = logging.getLogger(__name__)
fake = Faker()


# TODO A lot of setup duplication. Perhaps its a good idea to create a single factory on top of mixer or Factory boy


class PostsAPITests(APITestCase):
    """
    PostsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
        'openbook_common/fixtures/languages.json'
    ]

    def test_create_text_post(self):
        """
        should be able to create a text post and return 201
        """
        user = make_user()

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

    def test_create_text_post_with_only_link_should_not_throw_error(self):
        """
        should be able to create a text post with only a link and return 201
        """
        user = make_user()

        auth_token = user.auth_token.key

        post_text = 'https://www.okuna.io'

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

    def test_create_text_post_detect_language(self):
        """
        should be able to create a text post and detect its language and return 201
        """
        user = make_user()

        auth_token = user.auth_token.key

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.get(text=post_text).language.code is not None)

    def test_create_text_post_detects_mentions_once(self):
        """
        should be able to create a text post with a mention and detect it once
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_usernames = get_test_usernames()

        for test_username in test_usernames:
            test_user = make_user(username=test_username)
            post_text = 'Hello @' + test_user.username + ' @' + test_user.username

            data = {
                'text': post_text
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            post = Post.objects.get(text=post_text, creator_id=user.pk)

            self.assertEqual(PostUserMention.objects.filter(user_id=test_user.pk, post_id=post.pk).count(), 1)

    def test_create_text_detect_mention_is_case_insensitive(self):
        """
        should detect mention regardless of the username letter cases
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user(username='joel132')

        post_text = 'Hello @JoEl132'

        data = {
            'text': post_text,
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertTrue(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_text_post_ignores_non_existing_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames when creating a post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        fake_username = 'nonexistinguser'
        post_text = 'Hello @' + fake_username

        data = {
            'text': post_text
        }
        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertEqual(PostUserMention.objects.filter(post_id=post.pk).count(), 0)

    def test_create_text_post_creates_mention_notifications(self):
        """
        should be able to create a text post with a mention notification
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_user = make_user()
        post_text = 'Hello @' + test_user.username

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.get(text=post_text, creator_id=user.pk)

        post_user_mention = PostUserMention.objects.get(user_id=test_user.pk, post_id=post.pk)

        self.assertEqual(PostUserMentionNotification.objects.filter(post_user_mention_id=post_user_mention.pk,
                                                                    notification__owner_id=test_user.pk,
                                                                    notification__notification_type=Notification.POST_USER_MENTION).count(),
                         1)

    def test_create_text_post_does_not_detect_mention_if_encircled(self):
        """
        should not detect mention if the post is encircled and the mentioned person is outside the circle
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)
        circle = make_circle(creator=user)

        mentioned_user = make_user()

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertFalse(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_text_detect_mention_if_encircled_and_part_of(self):
        """
        should detect mention if the post is encircled and the mentioned person is in the circle
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)
        circle = make_circle(creator=user)

        mentioned_user = make_user()

        user.connect_with_user_with_id(user_id=mentioned_user.pk, circles_ids=[circle.pk])
        mentioned_user.confirm_connection_with_user_with_id(user_id=user.pk)

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertTrue(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_text_detect_mention_if_public(self):
        """
        should detect mention if the post is public
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()

        post_text = 'Hello @' + mentioned_user.username

        data = {
            'text': post_text,
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertTrue(PostUserMention.objects.filter(post_id=post.pk, user_id=mentioned_user.pk).exists())

    def test_create_text_post_does_not_detect_creator_mention(self):
        """
        should not detect mention if the mentioned person is the creator
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)
        circle = make_circle(creator=user)

        post_text = 'Hello @' + user.username

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertFalse(PostUserMention.objects.filter(post_id=post.pk, user_id=user.pk).exists())

    def test_create_post_is_added_to_world_circle(self):
        """
        the created text post should automatically added to world circle
        """
        user = make_user()

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
        user = make_user()

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
        user = make_user()

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
        user = make_user()

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

    def test_create_image_post_creates_hash(self):
        """
        creating an image post should create a hash and return 201
        """
        user = make_user()

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        filehash = sha256sum(filename=tmp_file.name)

        headers = make_authentication_headers_for_user(user)

        data = {
            'image': tmp_file
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertTrue(user.posts.count() == 1)

        self.assertTrue(user.posts.filter(pk=response_post_id, image__hash=filehash).exists())

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

    def test_create_video_post_creates_hash(self):
        """
        creating a video post creates a hash and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        video = SimpleUploadedFile("file.mp4", b"video_file_content", content_type="video/mp4")

        filehash = sha256sum(file=video.file)

        data = {
            'video': video
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.posts.filter(pk=response_post_id, video__hash=filehash))

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

    def test_create_public_draft_post(self):
        """
        should be able to create a public draft post and return 201
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        data = {
            'text': post_text,
            'is_draft': True
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertEqual(user.posts.filter(text=post_text, pk=response_post_id, status=Post.STATUS_DRAFT).count(), 1)

    def test_create_draft_post_in_circle(self):
        """
        should be able to create a draft post in an specified circle and return 201
        """
        user = make_user()

        circle = mixer.blend(Circle, creator=user)

        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)

        data = {
            'text': post_text,
            'circle_id': circle.pk,
            'is_draft': True
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(user.posts.filter(text=post_text, status=Post.STATUS_DRAFT, circles__id=circle.pk).count(), 1)

    def test_get_all_posts(self):
        """
        should be able to retrieve all posts
        """

        # BEWARE The max count for the API is 20. If we are checking for more than 20
        # posts, it will fail

        user = make_user()
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
        user = make_user()
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
            user_in_circle = make_user()
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

        user = make_user()
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
            user_in_list = make_user()
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
        user = make_user()
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

    def test_get_all_posts_with_min_id_and_count(self):
        """
        should be able to retrieve all posts with a min id and count
        """
        user = make_user()
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

        min_id = 10

        count = 3

        response = self.client.get(url, {
            'count': count,
            'min_id': min_id
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(count, len(response_posts))

        for response_post in response_posts:
            response_post_id = response_post.get('id')
            self.assertIn(response_post_id, all_posts_ids)
            self.assertTrue(response_post_id > min_id)

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

    def test_can_retrieve_own_community_post(self):
        """
        should be able to retrieve an own post posted to a community
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)

        post_text = make_fake_post_text()

        user.create_community_post(community_name=community.name, text=make_fake_post_text())

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        response_post_id = response_post['id']

        retrieved_post = Post.objects.get(pk=response_post_id)

        self.assertEqual(retrieved_post.community_id, community.pk)
        self.assertTrue(retrieved_post.text, post_text)

    def test_does_not_retrieve_duplicate_connections_posts_when_multiple_circles(self):
        """
        should not retrieve duplicate connections posts when posted to multiple circles
        """
        user = make_user()
        user_to_connect_to = make_user()

        circle = make_circle(creator=user)

        user.connect_with_user_with_id(user_id=user_to_connect_to.pk, circles_ids=[circle.pk])

        user_to_connect_to.confirm_connection_with_user_with_id(user_id=user.pk, )

        post = user.create_encircled_post(text=make_fake_post_text(),
                                          circles_ids=[circle.pk, user.connections_circle_id])

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_moderated_approved_community_posts(self):
        """
        should not be able to retrieve moderated approved community posts
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5
        post_reporter = make_user()
        report_category = make_moderation_category()

        for i in range(0, number_of_posts):
            post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
            post_reporter.report_post(post=post, category_id=report_category.pk)
            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                       category_id=report_category.pk)
            community_creator.approve_moderated_object(moderated_object=moderated_object)
        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_can_retrieve_moderated_rejected_community_posts(self):
        """
        should not be able to retrieve moderated rejected community posts
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5
        post_reporter = make_user()
        report_category = make_moderation_category()
        posts_ids = []

        for i in range(0, number_of_posts):
            post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
            posts_ids.append(post.pk)
            post_reporter.report_post(post=post, category_id=report_category.pk)
            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                       category_id=report_category.pk)
            community_creator.reject_moderated_object(moderated_object=moderated_object)
        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_posts))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_can_retrieve_moderated_pending_community_posts(self):
        """
        should not be able to retrieve moderated pending community posts
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5
        post_reporter = make_user()
        report_category = make_moderation_category()
        posts_ids = []

        for i in range(0, number_of_posts):
            post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
            posts_ids.append(post.pk)
            post_reporter.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(posts_ids), len(response_posts))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_cant_retrieve_soft_deleted_community_posts(self):
        """
        should not be able to retrieve soft deleted community posts
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5

        for i in range(0, number_of_posts):
            post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
            post.soft_delete()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_soft_deleted_following_user_posts(self):
        """
        should not be able to retrieve soft deleted following user posts
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        following_user_post.soft_delete()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_soft_deleted_following_user_posts_when_filtering(self):
        """
        should not be able to retrieve soft deleted following user posts when filtering
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        following_user_post.soft_delete()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'list_id': follow_list.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_soft_deleted_connected_user_posts(self):
        """
        should not be able to retrieve soft deleted connected user posts
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

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_soft_deleted_connected_user_posts_when_filtering(self):
        """
        should not be able to retrieve soft deleted connected user posts when filtering
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

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'circle_id': connected_user_post_circle.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_connected_user_posts(self):
        """
        should not be able to retrieve reported connected user posts
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

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_connected_user_posts_when_filtering(self):
        """
        should not be able to retrieve reported connected user posts when filtering
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

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'circle_id': connected_user_post_circle.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_following_user_posts(self):
        """
        should not be able to retrieve reported following user posts
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        user.report_post(post=following_user_post, category_id=make_moderation_category().pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_following_user_posts_when_filtering(self):
        """
        should not be able to retrieve reported following user posts when filtering
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        user.report_post(post=following_user_post, category_id=make_moderation_category().pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'list_id': follow_list.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_community_posts(self):
        """
        should not be able to retrieve reported community posts
        """
        user = make_user()

        community = make_community()

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5
        report_category = make_moderation_category()

        for i in range(0, number_of_posts):
            post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
            user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def _get_url(self):
        return reverse('posts')


class TrendingPostsAPITests(APITestCase):
    """
    TrendingPostsAPITests
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_displays_community_posts_only(self):
        """
        should display community posts only and return 200
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['id'], post.pk)

    def test_does_not_display_closed_community_posts(self):
        """
        should not display community posts that are closed
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two.is_closed = True
        post_two.save()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['id'], post.pk)

    def test_does_not_display_post_from_community_banned_from(self):
        """
        should not display posts from a community banned from and return 200
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_post_of_blocked_user(self):
        """
        should not be able to retrieve posts of a blocked user
        """
        user = make_user()

        user_to_retrieve_posts_from = make_user()
        user_to_retrieve_posts_from.create_public_post(text=make_fake_post_text())

        user.follow_user_with_id(user_id=user_to_retrieve_posts_from.pk)

        user.block_user_with_id(user_id=user_to_retrieve_posts_from.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_post_of_blocking_user(self):
        """
        should not be able to retrieve posts of a blocking user
        """
        user = make_user()

        user_to_retrieve_posts_from = make_user()
        user_to_retrieve_posts_from.create_public_post(text=make_fake_post_text())

        user.follow_user_with_id(user_id=user_to_retrieve_posts_from.pk)

        user_to_retrieve_posts_from.block_user_with_id(user_id=user.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_post_of_blocked_community_staff_member(self):
        """
        should not be able to retrieve posts of a blocked community staff member
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.block_user_with_id(user_id=community_owner.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def _get_url(self):
        return reverse('trending-posts')
