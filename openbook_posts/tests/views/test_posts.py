# Create your tests here.
import tempfile
from unittest import mock

from PIL import Image
from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django_rq import get_worker
from faker import Faker
from rest_framework import status
from rq import SimpleWorker

from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

from openbook.settings import POST_MAX_LENGTH
from openbook_auth.models import User, UserNotificationsSubscription
import random

import logging
import json

from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_users, make_fake_post_text, \
    make_authentication_headers_for_user, make_circle, make_community, make_list, make_moderation_category, \
    get_test_usernames, get_test_videos, get_test_image, make_global_moderator, \
    make_fake_post_comment_text, make_reactions_emoji_group, make_emoji, make_hashtag_name, make_hashtag, \
    get_test_valid_hashtags, get_test_invalid_hashtags, get_post_links
from openbook_common.utils.helpers import sha256sum, normalize_url
from openbook_communities.models import Community
from openbook_hashtags.models import Hashtag
from openbook_lists.models import List
from openbook_moderation.models import ModeratedObject
from openbook_notifications.models import PostUserMentionNotification, Notification, UserNewPostNotification
from openbook_posts.jobs import curate_top_posts, curate_trending_posts
from openbook_posts.models import Post, PostUserMention, PostMedia, TopPost, TrendingPost, PostLink

logger = logging.getLogger(__name__)
fake = Faker()


# TODO A lot of setup duplication. Perhaps its a good idea to create a single factory on top of mixer or Factory boy


class PostsAPITests(OpenbookAPITestCase):
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

    def test_create_text_post_with_hashtag_creates_hashtag_if_not_exist(self):
        """
        when ccreating a post with a hashtag, should create it if not exists
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag_name()

        post_text = 'A hashtag #' + hashtag

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)
        created_hashtag = Hashtag.objects.get(name=hashtag)
        self.assertTrue(post.hashtags.filter(pk=created_hashtag.pk).exists())
        self.assertEqual(post.hashtags.all().count(), 1)

    def test_create_text_post_with_existing_hashtag_adds_it(self):
        """
        when creating a post with an existing hashtag, should add it
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag = make_hashtag()

        new_post_text = 'A hashtag #' + hashtag.name

        data = {
            'text': new_post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post = Post.objects.get(text=new_post_text, creator_id=user.pk)
        self.assertTrue(post.hashtags.filter(pk=hashtag.pk).exists())
        self.assertEqual(Hashtag.objects.filter(pk=hashtag.pk).count(), 1)
        self.assertEqual(post.hashtags.all().count(), 1)

    def test_create_text_post_with_repeated_hashtag_does_not_create_double_hashtags(self):
        """
        when creating a post with a repeated hashtag, doesnt create it twice
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        hashtag_name = make_hashtag_name()
        post_text = '#%s #%s' % (hashtag_name, hashtag_name)

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)
        hashtag = Hashtag.objects.get(name=hashtag_name)
        self.assertEqual(post.hashtags.all().count(), 1)
        self.assertEqual(post.hashtags.filter(name=hashtag.name).count(), 1)
        self.assertEqual(Hashtag.objects.filter(name=hashtag.name).count(), 1)

    def test_create_text_post_with_valid_hashtags_creates_them(self):
        """
        when creating a post with valid hashtags, should create them
        """
        user = make_user()

        valid_hashtags = get_test_valid_hashtags()

        for valid_hashtag in valid_hashtags:
            headers = make_authentication_headers_for_user(user=user)

            post_text = 'Valid hashtag #' + valid_hashtag

            data = {
                'text': post_text
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

            post = Post.objects.get(text=post_text, creator_id=user.pk)
            created_hashtag = Hashtag.objects.get(name=valid_hashtag)
            self.assertTrue(post.hashtags.filter(pk=created_hashtag.pk).exists())
            self.assertEqual(post.hashtags.all().count(), 1)

    def test_create_text_post_with_invalid_hashtags_does_not_create_them(self):
        """
        when creating a post with invalid hashtags, should not create them
        """
        user = make_user()

        invalid_hashtags = get_test_invalid_hashtags()

        for invalid_hashtag in invalid_hashtags:
            headers = make_authentication_headers_for_user(user=user)

            post_text = 'Invalid hashtag #' + invalid_hashtag

            data = {
                'text': post_text
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

            post = Post.objects.get(text=post_text, creator_id=user.pk)
            self.assertFalse(Hashtag.objects.filter(name=invalid_hashtag).exists())
            self.assertFalse(post.hashtags.all().exists())

    def test_create_text_post_with_excedingly_long_hashtag_should_not_created_it(self):
        """
        when creating a post with an excedingly long hashtag, should not create it
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        long_hashtag = ''.join(['a' for item in range(0, settings.HASHTAG_NAME_MAX_LENGTH + 1)])
        post_text = 'Long hashtag #' + long_hashtag

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertFalse(Post.objects.filter(text=post_text).exists())
        self.assertFalse(Hashtag.objects.filter(name=long_hashtag).exists())

    def test_create_text_post_with_more_hashtags_than_allowed_should_not_create_it(self):
        """
        when creating a post with exceeding hashtags, should not create it
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)
        post_hashtags = []

        for i in range(0, settings.POST_MAX_HASHTAGS + 1):
            hashtag = '#%s' % make_hashtag_name()
            post_hashtags.append(hashtag)

        post_text = ' '.join(post_hashtags)

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertFalse(Post.objects.filter(text=post_text).exists())

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

    def test_create_text_detect_mention_ignores_casing_of_username(self):
        """
        should detect mention regardless of the casing of the username
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user(username='Joel')

        post_text = 'Hello @joel'

        data = {
            'text': post_text,
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        post = Post.objects.get(text=post_text, creator_id=user.pk)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

    def test_create_text_post_detects_all_urls(self):
        """
        should detect different links in post text and create post links models from them
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        links = get_post_links()

        post_text = " | ".join(links)

        data = {
            'text': post_text
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)
        post_links = PostLink.objects.filter(post_id=post.pk)
        result_links = [post_link.link for post_link in post_links]

        self.assertEqual(len(result_links), len(links))
        for link in links:
            link = normalize_url(link)
            self.assertTrue(link in result_links)

    def test_create_text_post_does_not_skips_http_urls(self):
        """
        should not skip http urls in post text while creating post links models from them
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post_text = 'http://unsafe.com/'

        data = {
            'text': post_text
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(text=post_text, creator_id=user.pk)
        post_links = PostLink.objects.filter(post_id=post.pk)
        result_links = [post_link.link for post_link in post_links]

        self.assertTrue(len(result_links), 1)

        result_link = result_links[0]

        self.assertEqual(result_link, post_text)

        self.assertEqual(len(result_links), 1)

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

        # To be removed
        self.assertTrue(hasattr(created_post, 'image'))

        self.assertTrue(created_post.status, Post.STATUS_PUBLISHED)

        post_media_image = created_post.media.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_IMAGE)

        post_image = post_media_image.content_object

        self.assertTrue(hasattr(post_image, 'image'))

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

        # To be removed
        self.assertTrue(hasattr(created_post, 'image'))

        self.assertTrue(created_post.status, Post.STATUS_PUBLISHED)

        post_media_image = created_post.media.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_IMAGE)

        post_image = post_media_image.content_object

        self.assertTrue(hasattr(post_image, 'image'))

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

        media = PostMedia.objects.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_IMAGE)
        self.assertEqual(media.content_object.hash, filehash)

    def test_create_video_post(self):
        """
        should be able to create a video post and return 201
        """

        test_videos = get_test_videos()

        for test_video in test_videos:
            with open(test_video['path'], 'rb') as file:
                user = make_user()
                headers = make_authentication_headers_for_user(user)

                data = {
                    'video': file
                }

                url = self._get_url()

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                response_post = json.loads(response.content)

                response_post_id = response_post.get('id')

                self.assertTrue(user.posts.count() == 1)

                created_post = user.posts.filter(pk=response_post_id).get()

                self.assertTrue(created_post.status, Post.STATUS_PROCESSING)

                get_worker('high', worker_class=SimpleWorker).work(burst=True)

                created_post.refresh_from_db()

                self.assertTrue(created_post.status, Post.STATUS_PUBLISHED)

                post_media_video = created_post.media.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_VIDEO)

                self.assertTrue(post_media_video.content_object.format_set.exists())

    def test_create_video_post_creates_hash(self):
        """
        creating a video post creates a hash and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        test_video = get_test_videos()[0]

        with open(test_video['path'], 'rb') as file:
            filehash = sha256sum(file=file)

            data = {
                'video': file
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            response_post = json.loads(response.content)

            response_post_id = response_post.get('id')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            media = PostMedia.objects.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_VIDEO)
            self.assertEqual(media.content_object.hash, filehash)

    def test_create_video_post_creates_thumbnail(self):
        """
        creating a video post creates a thumbnail and return 201
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        for test_video in get_test_videos():
            with open(test_video['path'], 'rb') as file:
                data = {
                    'video': file
                }

                url = self._get_url()

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                response_post = json.loads(response.content)

                response_post_id = response_post.get('id')

                media = PostMedia.objects.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_VIDEO)
                self.assertIsNotNone(media.content_object.thumbnail)
                self.assertIsNotNone(media.content_object.thumbnail_width)
                self.assertIsNotNone(media.content_object.thumbnail_height)

    def test_create_video_and_text_post(self):
        """
        should be able to create a video and text post and return 201
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        test_video = get_test_videos()[0]

        with open(test_video['path'], 'rb') as file:
            post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

            data = {
                'text': post_text,
                'video': file
            }

            url = self._get_url()

            response = self.client.put(url, data, **headers, format='multipart')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response_post = json.loads(response.content)

            response_post_id = response_post.get('id')

            self.assertTrue(user.posts.count() == 1)

            created_post = user.posts.filter(pk=response_post_id).get()

            self.assertTrue(created_post.status, Post.STATUS_PROCESSING)

            self.assertEqual(created_post.text, post_text)

            get_worker('high', worker_class=SimpleWorker).work(burst=True)

            created_post.refresh_from_db()

            self.assertTrue(created_post.status, Post.STATUS_PUBLISHED)

            post_media_video = created_post.media.get(post_id=response_post_id, type=PostMedia.MEDIA_TYPE_VIDEO)

            self.assertTrue(post_media_video.content_object.format_set.exists())

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

    def test_create_post_publishes_post_by_default(self):
        """
        should be able to create a post and have it automatically published
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        data = {
            'text': post_text
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertEqual(1, user.posts.filter(pk=response_post_id, status=Post.STATUS_PUBLISHED).count())

    def test_can_create_draft_post_with_no_text_image_nor_video(self):
        """
        should be able to create a draft post with no text, image nor video and return 201
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        data = {
            'is_draft': True
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_post = json.loads(response.content)

        response_post_id = response_post.get('id')

        self.assertEqual(1, user.posts.filter(pk=response_post_id, status=Post.STATUS_DRAFT).count())

    def test_cant_create_non_draft_post_with_no_text_image_nor_video(self):
        """
        should be able to create a draft post with no text, image nor video and return 201
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        post_text = make_fake_post_text()

        data = {
            # Its default
            # 'is_draft': False
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.posts.filter(text=post_text).exists())

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

        self.assertEqual(len(created_posts_ids), len(response_posts))

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_get_all_public_posts_for_public_user_unauthenticated(self):
        """
        should be able to retrieve all the public posts of an specific public visibility user
        being unauthenticated and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PUBLIC)

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

    def test_cant_get_public_posts_for_private_user_unauthenticated(self):
        """
        should not be able to retrieve the public posts of an specific private visibility user
        being unauthenticated and return 400
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PRIVATE)

        amount_of_user_public_posts = random.randint(1, 5)

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user.username
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_get_public_posts_for_okuna_visibility_user_authenticated(self):
        """
        should be able to retrieve the public posts of an specific okuna visibility user
        being authenticated and return 400
        """

        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        user_to_retrieve_posts_from = make_user(visibility=User.VISIBILITY_TYPE_OKUNA)

        amount_of_user_public_posts = random.randint(1, 5)

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user_to_retrieve_posts_from.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user_to_retrieve_posts_from.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), len(public_posts_ids))

        response_posts_ids = [response_post['id'] for response_post in response_posts]

        for public_post_id in public_posts_ids:
            self.assertIn(public_post_id, response_posts_ids)

    def test_cant_get_public_posts_for_okuna_visibility_user_unauthenticated(self):
        """
        should not be able to retrieve the public posts of an specific okuna visibility user
        being unauthenticated and return 400
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_OKUNA)

        amount_of_user_public_posts = random.randint(1, 5)

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user.username
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_get_public_posts_for_public_visibility_user_authenticated(self):
        """
        should be able to retrieve the public posts of an specific public visibility user
        being authenticated and return 400
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user=user)

        user_to_retrieve_posts_from = make_user(visibility=User.VISIBILITY_TYPE_PUBLIC)

        amount_of_user_public_posts = random.randint(1, 5)

        public_posts_ids = []

        for i in range(amount_of_user_public_posts):
            post_text = make_fake_post_text()
            public_post = user_to_retrieve_posts_from.create_public_post(text=post_text)
            public_posts_ids.append(public_post.pk)

        url = self._get_url()

        response = self.client.get(url, {
            'username': user_to_retrieve_posts_from.username
        }, **headers)

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

    def test_filter_public_community_post_from_own_posts_when_not_community_posts_visible(self):
        """
        should filter public community posts when community_posts_visible is false and return 200
        """
        user = make_user()
        user.update(community_posts_visible=False)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PUBLIC)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

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

    def test_filter_private_community_post_from_own_posts_when_not_community_posts_visible(self):
        """
        should filter public community posts when community_posts_visible is false and return 200
        """
        user = make_user()
        user.update(community_posts_visible=False)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

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

    def test_retrieve_own_public_community_post_from_own_posts_when_community_posts_visible(self):
        """
        should retrieve our own public community posts when community_posts_visible is true and return 200
        """
        user = make_user()
        user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PUBLIC)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

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

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_retrieve_private_community_post_from_own_posts_when_community_posts_visible(self):
        """
        should retrieve the private community posts when community_posts_visible is true and return 200
        """
        user = make_user()
        user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

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

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_filter_public_community_post_from_foreign_user_posts_when_not_community_posts_visible(self):
        """
        should filter public community posts from foreign user when community_posts_visible is false and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=False)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PUBLIC)

        foreign_user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_filter_private_community_post_from_foreign_user_posts_when_not_community_posts_visible(self):
        """
        should filter private community posts from foreign user when community_posts_visible is false and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=False)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=foreign_user.username,
                                                                         community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_filter_private_joined_community_post_from_foreign_user_posts_when_not_community_posts_visible(self):
        """
        should filter private joined community posts from foreign user when community_posts_visible is false and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=False)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=foreign_user.username,
                                                                         community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_retrieve_public_community_post_from_foreign_user_posts_when_community_posts_visible(self):
        """
        should retrieve public community posts from foreign user when community_posts_visible is true and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PUBLIC)

        foreign_user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_retrieve_joined_private_community_post_from_foreign_user_posts_when_community_posts_visible(self):
        """
        should retrieve joined private community posts from foreign user when community_posts_visible is true and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=foreign_user.username,
                                                                         community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        response_posts_ids = [post['id'] for post in response_posts]

        for post_id in created_posts_ids:
            self.assertIn(post_id, response_posts_ids)

    def test_filter_private_community_post_from_foreign_user_posts_when_community_posts_visible(self):
        """
        should filter private community posts from foreign user when community_posts_visible is true and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=foreign_user.username,
                                                                         community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)

        amount_of_community_posts = random.randint(1, 5)

        created_posts_ids = []

        for i in range(amount_of_community_posts):
            post = foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())
            created_posts_ids.append(post.pk)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_filter_excluded_public_community_post_from_foreign_user_posts(self):
        """
        should filter excluded public community from foreign user and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PUBLIC)

        foreign_user.join_community_with_name(community_name=community.name)

        foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())

        foreign_user.exclude_community_from_profile_posts(community=community)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_filter_excluded_private_community_member_of_post_from_foreign_user_posts(self):
        """
        should filter excluded private community member of post from foreign user and return 200
        """
        user = make_user()

        foreign_user = make_user()
        foreign_user.update(community_posts_visible=True)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_owner.invite_user_with_username_to_community_with_name(username=foreign_user.username,
                                                                         community_name=community.name)
        foreign_user.join_community_with_name(community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        foreign_user.create_community_post(community_name=community.name, text=make_fake_post_text())

        foreign_user.exclude_community_from_profile_posts(community=community)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {
            'username': foreign_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(len(response_posts), 0)

    def test_get_all_public_posts_for_public_visibility_user_unauthenticated_with_max_id_and_count(self):
        """
        should be able to retrieve all the public posts of an specific public visibility user
        using max_id and count being unauthenticated and return 200
        """
        user = make_user(visibility=User.VISIBILITY_TYPE_PUBLIC)

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

    def test_cant_retrieve_reported_community_posts_by_username(self):
        """
        should not be able to retrieve reported community posts by username
        """
        user = make_user()

        community = make_community()

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        report_category = make_moderation_category()

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        user.report_post(post=post, category_id=report_category.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': post_creator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_reported_and_approved_community_posts_by_username(self):
        """
        should not be able to retrieve and reported and approved community posts by username
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)
        post_reporter = make_user()

        report_category = make_moderation_category()

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_reporter.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)
        community_creator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': post_creator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_soft_deleted_community_posts_by_username(self):
        """
        should not be able to retrieve soft deleted community posts by username
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post.soft_delete()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': post_creator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_closed_community_posts_by_username(self):
        """
        should not be able to retrieve closed community posts by username
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        community_creator.close_post(post=post)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': post_creator.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_draft_public_community_posts(self):
        """
        should not be able to retrieve draft public community posts
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5

        for i in range(0, number_of_posts):
            post_creator.create_community_post(community_name=community.name, text=make_fake_post_text(),
                                               is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_draft_private_community_part_of_posts(self):
        """
        should not be able to retrieve draft private community posts
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_creator = make_user()

        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        community_creator.invite_user_with_username_to_community_with_name(username=post_creator.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        number_of_posts = 5

        for i in range(0, number_of_posts):
            post_creator.create_community_post(community_name=community.name, text=make_fake_post_text(),
                                               is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_following_user_draft_posts(self):
        """
        should not be able to retrieve following user draft posts
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_following_user_draft_posts_when_filtering(self):
        """
        should not be able to retrieve following user draft posts when filtering
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        following_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'list_id': follow_list.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_connected_user_draft_posts(self):
        """
        should not be able to retrieve connected user draft posts
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user.create_encircled_post(text=make_fake_post_text(),
                                             circles_ids=[connected_user_post_circle.pk],
                                             is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_connected_user_draft_posts_when_filtering(self):
        """
        should not be able to retrieve connected user draft posts when filtering
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user.create_encircled_post(text=make_fake_post_text(),
                                             circles_ids=[connected_user_post_circle.pk], is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'circle_id': connected_user_post_circle.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_public_community_draft_posts(self):
        """
        should not be able to retrieve public community draft posts
        """
        user = make_user()
        community = make_community()
        community_member = make_user()
        user.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)

        community_member.create_community_post(text=make_fake_post_text(), is_draft=True, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_private_community_part_of_draft_posts(self):
        """
        should not be able to retrieve private community part of draft posts
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_creator)
        community_member = make_user()

        community_creator.invite_user_with_username_to_community_with_name(username=community_member.username,
                                                                           community_name=community.name)
        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)

        community_member.create_community_post(text=make_fake_post_text(), is_draft=True, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_public_community_processing_posts(self):
        """
        should not be able to retrieve public community processing posts
        """
        user = make_user()
        community = make_community()
        community_member = make_user()
        user.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            community_member.create_community_post(text=make_fake_post_text(), image=file,
                                                   community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_private_community_part_of_processing_posts(self):
        """
        should not be able to retrieve private community part of processing posts
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_creator)
        community_member = make_user()

        community_creator.invite_user_with_username_to_community_with_name(username=community_member.username,
                                                                           community_name=community.name)
        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)
        community_member.join_community_with_name(community_name=community.name)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            community_member.create_community_post(text=make_fake_post_text(), image=file,
                                                   community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_connected_user_draft_posts_by_username(self):
        """
        should not be able to retrieve connected user draft posts by username
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user.create_encircled_post(text=make_fake_post_text(),
                                             circles_ids=[connected_user_post_circle.pk], is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': connected_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_following_user_draft_posts_by_username(self):
        """
        should not be able to retrieve following user draft posts by username
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        following_user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': following_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_own_reported_and_approved_community_posts_by_username(self):
        """
        should not be able to retrieve own approved and reported posts by username
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        post_reporter = make_user()

        report_category = make_moderation_category()

        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_reporter.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)
        community_creator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_own_reported_and_approved_posts_by_username(self):
        """
        should not be able to retrieve own approved and reported posts by username
        """
        user = make_user()

        global_moderator = make_global_moderator()

        post_reporter = make_user()

        report_category = make_moderation_category()

        post = user.create_public_post(text=make_fake_post_text())
        post_reporter.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_comment_counts_on_community_post_should_exclude_blocked_users(self):
        """
        should not count blocked users that are not admins in the comment counts on a community post
        """
        user = make_user()
        blocked_user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)

        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]
        comments_count = response_post['comments_count']
        self.assertEqual(comments_count, 0)

    def test_comment_counts_on_community_post_should_include_blocked_users_if_they_are_admins(self):
        """
        should count blocked users that ARE admins of that community in the comment counts on a community post
        """
        user = make_user()
        blocked_user = make_user()

        community = make_community(creator=blocked_user)

        user.join_community_with_name(community_name=community.name)

        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        blocked_user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=blocked_user.pk)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]
        comments_count = response_post['comments_count']
        self.assertEqual(comments_count, 1)

    def test_comment_counts_on_posts_should_include_replies(self):
        """
        should count replies in the comment counts on posts
        """
        user = make_user()
        replier = make_user()

        post = user.create_public_post(text=make_fake_post_text())

        post_comment = user.comment_post_with_id(post_id=post.pk, text=make_fake_post_comment_text())

        replier.reply_to_comment_with_id_for_post_with_uuid(post_comment_id=post_comment.pk,
                                                            post_uuid=post.uuid,
                                                            text=make_fake_post_comment_text())

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]
        comments_count = response_post['comments_count']
        self.assertTrue(comments_count, 2)

    def test_cant_retrieve_own_draft_posts_by_username(self):
        """
        should not be able to retrieve own draft posts by username
        """
        user = make_user()

        user.create_public_post(text=make_fake_post_text(), is_draft=True)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_own_public_community_draft_posts_by_username(self):
        """
        should not be able to retrieve own public community draft posts by username
        """
        user = make_user()
        community = make_community()
        user.join_community_with_name(community_name=community.name)

        user.create_community_post(text=make_fake_post_text(), is_draft=True, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_own_private_community_part_of_draft_posts_by_username(self):
        """
        should not be able to retrieve own private community part of draft posts by username
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_creator)

        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        user.create_community_post(text=make_fake_post_text(), is_draft=True, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_public_community_posts(self, process_post_media_mock):
        """
        should not be able to retrieve processing public community posts
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post_creator.create_community_post(community_name=community.name, text=make_fake_post_text(),
                                               image=file)

            url = self._get_url()
            headers = make_authentication_headers_for_user(user)
            response = self.client.get(url, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_posts = json.loads(response.content)

            self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_processing_private_community_part_of_posts(self, mock):
        """
        should not be able to retrieve processing private community posts
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_creator = make_user()

        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        community_creator.invite_user_with_username_to_community_with_name(username=post_creator.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post_creator.create_community_post(community_name=community.name, text=make_fake_post_text(),
                                               image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_following_user_processing_posts(self, mock):
        """
        should not be able to retrieve following user processing posts
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            following_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_following_user_processing_posts_when_filtering(self, mock):
        """
        should not be able to retrieve following user processing posts when filtering
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            following_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'list_id': follow_list.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_connected_user_processing_posts(self, mock):
        """
        should not be able to retrieve connected user processing posts
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            connected_user.create_encircled_post(text=make_fake_post_text(),
                                                 circles_ids=[connected_user_post_circle.pk],
                                                 image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_connected_user_processing_posts_when_filtering(self, mock):
        """
        should not be able to retrieve connected user processing posts when filtering
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            connected_user.create_encircled_post(text=make_fake_post_text(),
                                                 circles_ids=[connected_user_post_circle.pk], image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'circle_id': connected_user_post_circle.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_connected_user_processing_posts_by_username(self, file):
        """
        should not be able to retrieve connected user processing posts by username
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            connected_user.create_encircled_post(text=make_fake_post_text(),
                                                 circles_ids=[connected_user_post_circle.pk], image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': connected_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_following_user_processing_posts_by_username(self, mock):
        """
        should not be able to retrieve following user processing posts by username
        """
        user = make_user()

        following_user = make_user()
        follow_list = make_list(creator=user)
        user.follow_user_with_id(user_id=following_user.pk, lists_ids=[follow_list.pk])

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            following_user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': following_user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_own_processing_posts_by_username(self, mock):
        """
        should not be able to retrieve own processing posts by username
        """
        user = make_user()

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            user.create_public_post(text=make_fake_post_text(), image=file)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_own_public_community_processing_posts_by_username(self, mock):
        """
        should not be able to retrieve own public community processing posts by username
        """
        user = make_user()
        community = make_community()
        user.join_community_with_name(community_name=community.name)

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            user.create_community_post(text=make_fake_post_text(), image=file, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    @mock.patch('openbook_posts.jobs.process_post_media')
    def test_cant_retrieve_own_private_community_part_of_processing_posts_by_username(self, mock):
        """
        should not be able to retrieve own private community part of processing posts by username
        """
        user = make_user()
        community_creator = make_user()
        community = make_community(type=Community.COMMUNITY_TYPE_PRIVATE, creator=community_creator)

        community_creator.invite_user_with_username_to_community_with_name(username=user.username,
                                                                           community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        test_image = get_test_image()
        with open(test_image['path'], 'rb') as file:
            file = File(file)
            user.create_community_post(text=make_fake_post_text(), image=file, community_name=community.name)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, {
            'username': user.username
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_create_post_notifies_subscribers(self):
        """
        should notify subscribers when a post is created
        """
        user = make_user()
        subscriber = make_user()
        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)
        data = {'text': post_text}

        subscriber.enable_new_post_notifications_for_user_with_username(user.username)

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')

        user_notifications_subscription = UserNotificationsSubscription.objects.get(subscriber=subscriber, user=user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserNewPostNotification.objects.filter(
            user_notifications_subscription=user_notifications_subscription).count() == 1)

    def test_create_post_does_not_notify_subscribers_if_post_creator_is_blocked(self):
        """
        should NOT notify subscribers if creator is blocked when a post is created
        """
        user = make_user()
        subscriber = make_user()
        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)
        data = {'text': post_text}

        subscriber.enable_new_post_notifications_for_user_with_username(user.username)
        subscriber.block_user_with_id(user_id=user.pk)

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        response_post = json.loads(response.content)
        post = Post.objects.get(id=response_post['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserNewPostNotification.objects.filter(
            post=post).count() == 0)

    def test_create_post_does_not_notify_subscribers_if_they_have_been_blocked(self):
        """
        should NOT notify subscribers if creator has blocked them
        """
        user = make_user()
        subscriber = make_user()
        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)

        headers = make_authentication_headers_for_user(user)
        data = {'text': post_text}

        subscriber.enable_new_post_notifications_for_user_with_username(user.username)
        user.block_user_with_id(user_id=subscriber.pk)

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')
        response_post = json.loads(response.content)
        post = Post.objects.get(id=response_post['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserNewPostNotification.objects.filter(
            post=post).count() == 0)

    def test_encircled_post_should_notify_only_subscribers_in_that_circle(self):
        """
        should only notify subscribers in a circle if encircled post
        """
        post_creator = make_user()
        subscriber = make_user()
        other_subscriber = make_user()
        post_text = fake.text(max_nb_chars=POST_MAX_LENGTH)
        headers = make_authentication_headers_for_user(post_creator)
        circle = mixer.blend(Circle, creator=post_creator)

        # connect with subscriber and add them to circle
        subscriber.connect_with_user_with_id(post_creator.pk)
        post_creator.confirm_connection_with_user_with_id(user_id=subscriber.pk, circles_ids=[circle.pk])

        # both users subscribe
        subscriber.enable_new_post_notifications_for_user_with_username(post_creator.username)
        other_subscriber.enable_new_post_notifications_for_user_with_username(post_creator.username)

        data = {
            'text': post_text,
            'circle_id': circle.pk
        }

        url = self._get_url()
        response = self.client.put(url, data, **headers, format='multipart')

        other_subscriber_notifications_subscription = UserNotificationsSubscription.objects.get(
            subscriber=other_subscriber, user=post_creator)

        subscriber_notifications_subscription = UserNotificationsSubscription.objects.get(
            subscriber=subscriber, user=post_creator)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserNewPostNotification.objects.filter(
            user_notifications_subscription=other_subscriber_notifications_subscription).count() == 0)
        self.assertTrue(UserNewPostNotification.objects.filter(
            user_notifications_subscription=subscriber_notifications_subscription).count() == 1)

    def _get_url(self):
        return reverse('posts')


class TrendingPostsAPITests(OpenbookAPITestCase):
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

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        curate_trending_posts()

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['post']['id'], post.pk)
        self.assertTrue(TrendingPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_curate_community_posts_with_less_than_min_reactions(self):
        """
        should not curate community posts with less than minimum reactions and return 200
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        headers = make_authentication_headers_for_user(user)

        curate_trending_posts()

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))
        self.assertFalse(TrendingPost.objects.filter(post__id=post.pk).exists())

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

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)
        user.react_to_post_with_id(post_id=post_two.pk, emoji_id=emoji.pk)

        curate_trending_posts()

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(1, len(response_posts))

        response_post = response_posts[0]

        self.assertEqual(response_post['post']['id'], post.pk)
        self.assertFalse(TrendingPost.objects.filter(post__id=post_two.pk).exists())
        self.assertTrue(TrendingPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_display_post_from_community_banned_from(self):
        """
        should not display posts from a community banned from and return 200
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)

        user.join_community_with_name(community_name=community.name)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        headers = make_authentication_headers_for_user(user)

        curate_trending_posts()

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
        community = make_community(creator=user)
        user_to_retrieve_posts_from = make_user()
        user_to_retrieve_posts_from.join_community_with_name(community_name=community.name)

        post = user_to_retrieve_posts_from.create_community_post(text=make_fake_post_text(),
                                                                 community_name=community.name)

        # react once, min required while testing
        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        user.block_user_with_id(user_id=user_to_retrieve_posts_from.pk)

        curate_trending_posts()

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
        community = make_community(creator=user)
        user_to_retrieve_posts_from = make_user()
        user_to_retrieve_posts_from.join_community_with_name(community_name=community.name)

        post = user_to_retrieve_posts_from.create_community_post(text=make_fake_post_text(),
                                                                 community_name=community.name)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        user_to_retrieve_posts_from.block_user_with_id(user_id=user.pk)

        curate_trending_posts()

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

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)
        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        # block user
        user.block_user_with_id(user_id=community_owner.pk)

        curate_trending_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_does_not_curate_encircled_posts(self):
        """
        should not curate encircled posts in trending posts
        """
        post_creator = make_user()
        user = make_user()

        circle = make_circle(creator=post_creator)

        post_creator.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=post_creator.pk)

        post_text = make_fake_post_text()
        post = post_creator.create_encircled_post(text=post_text, circles_ids=[circle.pk])

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        trending_posts = TrendingPost.objects.all()
        self.assertEqual(0, len(trending_posts))
        self.assertFalse(TrendingPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_curate_private_community_posts(self):
        """
        should not curate private community posts in trending posts
        """
        user = make_user()

        community = make_community(creator=user, type=Community.COMMUNITY_TYPE_PRIVATE)
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        trending_posts = TrendingPost.objects.all()
        self.assertEqual(0, len(trending_posts))
        self.assertFalse(TrendingPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_return_recently_turned_private_community_posts(self):
        """
        should not return recently turned private community posts in trending posts
        """
        user = make_user()

        community = make_community(creator=user, type=Community.COMMUNITY_TYPE_PUBLIC)
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        community.type = Community.COMMUNITY_TYPE_PRIVATE
        community.save()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        trending_posts = TrendingPost.objects.all()
        self.assertEqual(1, len(trending_posts))
        self.assertTrue(TrendingPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_display_curated_closed_community_posts(self):
        """
        should not display community posts that are closed after already curated in trending posts
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)
        user.react_to_post_with_id(post_id=post_two.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        post_two.is_closed = True
        post_two.save()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post.pk)

    def test_does_not_display_reported_community_posts_that_are_approved(self):
        """
        should not display community posts that are reported and approved by staff in trending posts
        """
        user = make_user()
        post_reporter = make_user()
        community = make_community(creator=user)
        post_reporter.join_community_with_name(community_name=community.name)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # report and approve the report for one post
        moderation_category = make_moderation_category()
        post_reporter.report_post(post=post, category_id=moderation_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=moderation_category.pk)
        user.approve_moderated_object(moderated_object=moderated_object)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)
        user.react_to_post_with_id(post_id=post_two.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post_two.pk)

        trending_posts = TrendingPost.objects.all()
        self.assertEqual(1, len(trending_posts))
        self.assertTrue(TrendingPost.objects.filter(post__id=post_two.pk).exists())

    def test_does_not_display_reported_community_posts_that_are_approved_after_curation(self):
        """
        should not display community posts that are reported and approved after already curated by staff in trending posts
        """
        user = make_user()
        post_reporter = make_user()
        community = make_community(creator=user)
        post_reporter.join_community_with_name(community_name=community.name)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # report and approve the report for one post
        moderation_category = make_moderation_category()
        post_reporter.report_post(post=post, category_id=moderation_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=moderation_category.pk)

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        user.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk)
        user.react_to_post_with_id(post_id=post_two.pk, emoji_id=emoji.pk)

        # curate trending posts
        curate_trending_posts()

        user.approve_moderated_object(moderated_object=moderated_object)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post_two.pk)

    def _get_url(self):
        return reverse('trending-posts-new')


class TopPostsAPITests(OpenbookAPITestCase):
    """
    TopPostsAPITests
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_displays_community_posts_only(self):
        """
        should display community posts only in top posts and return 200
        """
        user = make_user()
        community = make_community(creator=user)

        public_post = user.create_public_post(text=make_fake_post_text())
        community_post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(community_post, text=make_fake_post_comment_text())
        user.comment_post(public_post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], community_post.pk)

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=community_post.pk).exists())

    def test_excludes_joined_communities_if_true(self):
        """
        should display posts only from communities not joined by user if exclude_joined_communities is true
        """
        user = make_user()
        community_creator = make_user()
        user_community = make_community(creator=user)
        community = make_community(creator=community_creator)

        user_community_post = user.create_community_post(community_name=user_community.name, text=make_fake_post_text())
        community_post = community_creator.create_community_post(community_name=community.name,
                                                                 text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(user_community_post, text=make_fake_post_comment_text())
        community_creator.comment_post(community_post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, {'exclude_joined_communities': True}, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], community_post.pk)

        top_posts = TopPost.objects.all()
        self.assertEqual(2, len(top_posts))

    def test_does_not_display_excluded_community_posts(self):
        """
        should not display excluded community posts in top posts
        """
        user = make_user()
        community = make_community(creator=user)

        public_post = user.create_public_post(text=make_fake_post_text())
        community_post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(community_post, text=make_fake_post_comment_text())
        user.comment_post(public_post, text=make_fake_post_comment_text())

        user.exclude_community_with_name_from_top_posts(community.name)

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=community_post.pk).exists())

    def test_does_not_curate_encircled_posts(self):
        """
        should not curate encircled posts in top posts
        """
        post_creator = make_user()
        user = make_user()

        circle = make_circle(creator=post_creator)

        post_creator.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=post_creator.pk)

        post_text = make_fake_post_text()
        post = post_creator.create_encircled_post(text=post_text, circles_ids=[circle.pk])

        # comment on post to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(0, len(top_posts))
        self.assertFalse(TopPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_curate_private_community_posts(self):
        """
        should not curate private community posts in top posts
        """
        user = make_user()

        community = make_community(creator=user, type=Community.COMMUNITY_TYPE_PRIVATE)
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on post to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(0, len(top_posts))
        self.assertFalse(TopPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_return_recently_turned_private_community_posts(self):
        """
        should not return recently turned private community posts in top posts
        """
        user = make_user()

        community = make_community(creator=user, type=Community.COMMUNITY_TYPE_PUBLIC)
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on post to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        community.type = Community.COMMUNITY_TYPE_PRIVATE
        community.save()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_display_closed_community_posts(self):
        """
        should not display community posts that are closed in top posts
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two.is_closed = True
        post_two.save()

        # comment on both posts to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())
        user.comment_post(post_two, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post.pk)

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=post.pk).exists())

    def test_does_not_display_curated_closed_community_posts(self):
        """
        should not display community posts that are closed after already curated in top posts
        """
        user = make_user()
        community = make_community(creator=user)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())
        user.comment_post(post_two, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        post_two.is_closed = True
        post_two.save()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post.pk)

    def test_does_not_display_reported_community_posts_that_are_approved(self):
        """
        should not display community posts that are reported and approved by staff in top posts
        """
        user = make_user()
        post_reporter = make_user()
        community = make_community(creator=user)
        post_reporter.join_community_with_name(community_name=community.name)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())
        user.comment_post(post_two, text=make_fake_post_comment_text())

        # report and approve the report for one post
        moderation_category = make_moderation_category()
        post_reporter.report_post(post=post, category_id=moderation_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=moderation_category.pk)
        user.approve_moderated_object(moderated_object=moderated_object)

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post_two.pk)

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=post_two.pk).exists())

    def test_does_not_display_reported_community_posts_that_are_approved_after_curation(self):
        """
        should not display community posts that are reported and approved after already curated by staff in top posts
        """
        user = make_user()
        post_reporter = make_user()
        community = make_community(creator=user)
        post_reporter.join_community_with_name(community_name=community.name)

        user.create_public_post(text=make_fake_post_text())
        post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = user.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment on both posts to qualify for top
        user.comment_post(post, text=make_fake_post_comment_text())
        user.comment_post(post_two, text=make_fake_post_comment_text())

        # report and approve the report for one post
        moderation_category = make_moderation_category()
        post_reporter.report_post(post=post, category_id=moderation_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=moderation_category.pk)

        # curate top posts
        curate_top_posts()

        user.approve_moderated_object(moderated_object=moderated_object)

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))
        response_post = response_posts[0]
        self.assertEqual(response_post['post']['id'], post_two.pk)

    def test_does_not_display_post_from_community_banned_from(self):
        """
        should not display posts from a community banned from and return 200 in top posts
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)
        user.join_community_with_name(community_name=community.name)
        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        # comment on post to qualify for top
        community_owner.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        headers = make_authentication_headers_for_user(user)

        url = self._get_url()

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_post_of_blocked_user(self):
        """
        should not be able to retrieve posts of a blocked user in top posts
        """
        user = make_user()

        user_to_retrieve_posts_from = make_user()
        community = make_community(creator=user_to_retrieve_posts_from)
        post = user_to_retrieve_posts_from.create_community_post(community_name=community.name,
                                                                 text=make_fake_post_text())
        user_to_retrieve_posts_from.comment_post(post, text=make_fake_post_comment_text())

        user.follow_user_with_id(user_id=user_to_retrieve_posts_from.pk)
        user.block_user_with_id(user_id=user_to_retrieve_posts_from.pk)

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_cant_retrieve_post_of_blocking_user(self):
        """
        should not be able to retrieve posts of a blocking user in top posts
        """
        user = make_user()

        user_to_retrieve_posts_from = make_user()
        community = make_community(creator=user_to_retrieve_posts_from)
        post = user_to_retrieve_posts_from.create_community_post(community_name=community.name,
                                                                 text=make_fake_post_text())
        user_to_retrieve_posts_from.comment_post(post, text=make_fake_post_comment_text())

        user_to_retrieve_posts_from.block_user_with_id(user_id=user.pk)

        # curate top posts
        curate_top_posts()

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
        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        community_owner.comment_post(post, text=make_fake_post_comment_text())

        user.block_user_with_id(user_id=community_owner.pk)

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_posts = json.loads(response.content)

        self.assertEqual(0, len(response_posts))

    def test_should_have_minimum_comments_to_curate_as_top_post(self):
        """
        should not curate a post as top post unless it has minimum no of comments
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)
        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        # comment once, min comments required while testing
        community_owner.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        top_posts = TopPost.objects.all()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=post.pk).exists())

    def test_should_have_minimum_reactions_to_curate_as_top_post(self):
        """
        should not curate a post as top post unless it has minimum no of reactions
        """
        user = make_user()
        community_owner = make_user()

        community = make_community(creator=community_owner)
        post = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_two = community_owner.create_community_post(community_name=community.name, text=make_fake_post_text())

        emoji_group = make_reactions_emoji_group()
        emoji = make_emoji(group=emoji_group)

        # react once, min required while testing
        community_owner.react_to_post_with_id(post_id=post.pk, emoji_id=emoji.pk, )

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(1, len(response_posts))

        top_posts = TopPost.objects.all()
        self.assertEqual(1, len(top_posts))
        self.assertTrue(TopPost.objects.filter(post__id=post.pk).exists())

    def test_should_respect_max_id_param_for_top_posts(self):
        """
        should take into account max_id in when returning top posts
        """
        user = make_user()
        total_posts = 10

        community = make_community(creator=user)

        for i in range(total_posts):
            post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
            user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, {'max_id': 5}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(4, len(response_posts))

        for top_post in response_posts:
            self.assertTrue(top_post['id'] < 5)

    def test_should_respect_min_id_param_for_top_posts(self):
        """
        should take into account min_id in when returning top posts
        """
        user = make_user()
        total_posts = 10

        community = make_community(creator=user)

        for i in range(total_posts):
            post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
            user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, {'min_id': 5}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(5, len(response_posts))

        for top_post in response_posts:
            self.assertTrue(top_post['id'] > 5)

    def test_should_respect_count_param_for_top_posts(self):
        """
        should take into account count when returning top posts
        """
        user = make_user()
        total_posts = 10

        community = make_community(creator=user)

        for i in range(total_posts):
            post = user.create_community_post(community_name=community.name, text=make_fake_post_text())
            user.comment_post(post, text=make_fake_post_comment_text())

        # curate top posts
        curate_top_posts()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.get(url, {'count': 5}, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_posts = json.loads(response.content)
        self.assertEqual(5, len(response_posts))

    def _get_url(self):
        return reverse('top-posts')


class ProfilePostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    ProfilePostsExcludedCommunitiesAPI
    """

    def test_retrieve_excluded_communities(self):
        """
        should be able to retrieve all excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]
        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_profile_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_should_not_retrieve_non_excluded_communities(self):
        """
        should NOT retrieve non-excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), 0)

    def test_retrieve_excluded_communities_offset(self):
        """
        should be able to retrieve all excluded communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        communities = mixer.cycle(total_amount_of_communities).blend(Community, creator=user)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_profile_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def test_can_exclude_public_community(self):
        """
        should be able to exclude a public community from profile posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        url = self._get_url()

        data = {
            'community_name': community.name
        }

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(user.has_excluded_community_with_name_from_profile_posts(community_name=community.name))

    def test_can_exclude_private_community(self):
        """
        should be able to exclude a private community from profile posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type=Community.COMMUNITY_TYPE_PRIVATE)

        url = self._get_url()

        data = {
            'community_name': community.name
        }
        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(user.has_excluded_community_with_name_from_profile_posts(community_name=community.name))

    def test_cannot_exclude_community_already_excluded(self):
        """
        should not be able to exclude a community if already excluded from profile posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        user.exclude_community_with_name_from_profile_posts(community.name)

        url = self._get_url()

        data = {
            'community_name': community.name
        }

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(user.has_excluded_community_with_name_from_profile_posts(community_name=community.name))

    def _get_url(self):
        return reverse('profile-posts-excluded-communities')


class SearchProfilePostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchProfilePostsExcludedCommunitiesAPI
    """

    def test_can_search_excluded_communities_by_name(self):
        """
        should be able to search for excluded communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_profile_posts(community_name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            parsed_response = json.loads(response.content)
            self.assertEqual(len(parsed_response), 1)

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_excluded_communities_by_title(self):
        """
        should be able to search for excluded communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = mixer.blend(Community, title=community_title, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_profile_posts(community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            parsed_response = json.loads(response.content)
            self.assertEqual(len(parsed_response), 1)

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('search-profile-posts-excluded-communities')


class ProfilePostsExcludedCommunityAPITests(OpenbookAPITestCase):
    """
    ProfilePostsExcludedCommunityAPI
    """

    def test_can_remove_excluded_community(self):
        """
        should be able to remove an community exclusion
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        user.exclude_community_with_name_from_profile_posts(community.name)

        url = self._get_url(community=community)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(user.has_excluded_community_with_name_from_profile_posts(community_name=community.name))

    def test_cannot_remove_exclusion_for_community_if_not_excluded(self):
        """
        should not be able to remove an community exclusion, if the community is not excluded in the first place
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        url = self._get_url(community=community)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_excluded_community_with_name_from_profile_posts(community_name=community.name))

    def _get_url(self, community):
        return reverse('profile-posts-excluded-community', kwargs={
            'community_name': community.name
        })


class TopPostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    TopPostsExcludedCommunitiesAPI
    """

    def test_retrieve_excluded_communities(self):
        """
        should be able to retrieve all excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        communities_ids = [community.pk for community in communities]
        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_top_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), len(communities_ids))

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, communities_ids)

    def test_should_not_retrieve_non_excluded_communities(self):
        """
        should NOT retrieve non-excluded communities and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        communities = mixer.cycle(5).blend(Community, creator=user)
        for community in communities:
            user.join_community_with_name(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), 0)

    def test_retrieve_excluded_communities_offset(self):
        """
        should be able to retrieve all excluded communities with an offset return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        total_amount_of_communities = 10
        offset = 5

        communities = mixer.cycle(total_amount_of_communities).blend(Community, creator=user)

        offsetted_communities = communities[offset: total_amount_of_communities]
        offsetted_communities_ids = [community.pk for community in offsetted_communities]

        for community in communities:
            user.join_community_with_name(community_name=community.name)
            user.exclude_community_with_name_from_top_posts(community_name=community.name)

        url = self._get_url()
        response = self.client.get(url, {
            'offset': offset
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_communities = json.loads(response.content)

        self.assertEqual(len(response_communities), total_amount_of_communities - offset)

        for response_community in response_communities:
            response_community_id = response_community.get('id')
            self.assertIn(response_community_id, offsetted_communities_ids)

    def test_can_exclude_public_community(self):
        """
        should be able to exclude a public community from top posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        url = self._get_url()

        data = {
            'community_name': community.name
        }

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(user.has_excluded_community_with_name_from_top_posts(community_name=community.name))

    def test_cannot_exclude_private_community(self):
        """
        should be able to exclude a private community from top posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type=Community.COMMUNITY_TYPE_PRIVATE)

        url = self._get_url()

        data = {
            'community_name': community.name
        }
        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_excluded_community_with_name_from_top_posts(community_name=community.name))

    def test_cannot_exclude_community_already_excluded(self):
        """
        should not be able to exclude a community if already excluded from top posts
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        user.exclude_community_with_name_from_top_posts(community.name)

        url = self._get_url()

        data = {
            'community_name': community.name
        }

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(user.has_excluded_community_with_name_from_top_posts(community_name=community.name))

    def _get_url(self):
        return reverse('top-posts-excluded-communities')


class SearchTopPostsExcludedCommunitiesAPITests(OpenbookAPITestCase):
    """
    SearchTopPostsExcludedCommunitiesAPI
    """

    def test_can_search_excluded_communities_by_name(self):
        """
        should be able to search for excluded communities by their name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_name = fake.user_name().lower()
            community = mixer.blend(Community, name=community_name, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_top_posts(community_name)

            amount_of_characters_to_query = random.randint(1, len(community_name))
            query = community_name[0:amount_of_characters_to_query]

            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            parsed_response = json.loads(response.content)
            self.assertEqual(len(parsed_response), 1)

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['name'], community_name.lower())
            community.delete()

    def test_can_search_excluded_communities_by_title(self):
        """
        should be able to search for excluded communities by their title and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        amount_of_joined_communities_to_search_for = 5

        for i in range(0, amount_of_joined_communities_to_search_for):
            community_title = fake.user_name().lower()
            community = mixer.blend(Community, title=community_title, type=Community.COMMUNITY_TYPE_PUBLIC)

            user.exclude_community_with_name_from_top_posts(community.name)

            amount_of_characters_to_query = random.randint(1, len(community_title))
            query = community_title[0:amount_of_characters_to_query]

            final_query = ''
            for character in query:
                final_query = final_query + (character.upper() if fake.boolean() else character.lower())

            url = self._get_url()

            response = self.client.get(url, {
                'query': final_query
            }, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            parsed_response = json.loads(response.content)
            self.assertEqual(len(parsed_response), 1)

            retrieved_community = parsed_response[0]
            self.assertEqual(retrieved_community['title'], community_title.lower())
            community.delete()

    def _get_url(self):
        return reverse('search-top-posts-excluded-communities')


class TopPostsExcludedCommunityAPITests(OpenbookAPITestCase):
    """
    TopPostsExcludedCommunityAPI
    """

    def test_can_remove_excluded_community(self):
        """
        should be able to remove an community exclusion
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)
        user.exclude_community_with_name_from_top_posts(community.name)

        url = self._get_url(community=community)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(user.has_excluded_community_with_name_from_top_posts(community_name=community.name))

    def test_cannot_remove_exclusion_for_community_if_not_excluded(self):
        """
        should not be able to remove an community exclusion, if the community is not excluded in the first place
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        url = self._get_url(community=community)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_excluded_community_with_name_from_top_posts(community_name=community.name))

    def _get_url(self, community):
        return reverse('top-posts-excluded-community', kwargs={
            'community_name': community.name
        })
