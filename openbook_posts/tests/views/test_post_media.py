# Create your tests here.
import json
import tempfile

from PIL import Image
from django.conf import settings
from django.core.files import File
from django.urls import reverse
from django_rq import get_worker
from faker import Faker
from rest_framework import status
from rq import SimpleWorker

from openbook_common.tests.models import OpenbookAPITestCase
import random

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_user, get_test_videos, get_test_image, get_test_video, make_circle, make_community, get_test_images
from openbook_communities.models import Community
from openbook_posts.models import PostMedia, Post

logger = logging.getLogger(__name__)
fake = Faker()


class PostMediaAPITests(OpenbookAPITestCase):
    """
    PostMediaAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_add_media_image_to_draft_post(self):
        """
        should be able to add a media image to a draft post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        draft_post = user.create_public_post(is_draft=True)

        image_width = random.randint(100, 500)
        image_height = random.randint(100, 500)

        image = Image.new('RGB', (image_width, image_height))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'file': tmp_file
        }

        url = self._get_url(post=draft_post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        draft_post.refresh_from_db()

        self.assertEqual(draft_post.status, Post.STATUS_DRAFT)

        self.assertTrue(draft_post.media.exists())

        post_media = draft_post.media.all()

        self.assertEqual(len(post_media), 1)

        post_media_image = post_media[0]

        self.assertEqual(post_media_image.type, PostMedia.MEDIA_TYPE_IMAGE)

        self.assertEqual(post_media_image.order, 0)

        post_image = post_media_image.content_object

        self.assertTrue(hasattr(post_image, 'image'))

        self.assertEqual(post_image.width, image_width)
        self.assertEqual(post_image.width, image_width)

        # Not for long though
        self.assertTrue(hasattr(draft_post, 'image'))

    def test_can_add_media_video_to_draft_post(self):
        """
        should be able to add a media video to a draft post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        test_videos = get_test_videos()

        for test_video in test_videos:
            with open(test_video['path'], 'rb') as file:
                draft_post = user.create_public_post(is_draft=True)

                data = {
                    'file': file
                }

                url = self._get_url(post=draft_post)

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                draft_post.refresh_from_db()

                self.assertEqual(draft_post.status, Post.STATUS_DRAFT)

                self.assertTrue(draft_post.media.exists())

                post_media = draft_post.media.all()

                self.assertEqual(len(post_media), 1)

                post_media_video = post_media[0]

                self.assertEqual(post_media_video.type, PostMedia.MEDIA_TYPE_VIDEO)

                self.assertEqual(post_media_video.order, 0)

                post_video = post_media_video.content_object

                self.assertTrue(hasattr(post_video, 'file'))

    def test_cant_add_media_image_to_published_post(self):
        """
        should not be able to add a media image to a published post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post = user.create_public_post(text=make_fake_post_text())

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'file': tmp_file
        }

        url = self._get_url(post=post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(post.has_media())

    def test_cannot_add_media_to_draft_if_exceeds_settings_maximum(self):
        """
        should not be able to add a media item to a draft post if exceeds the settings maximums
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        draft_post = user.create_public_post(is_draft=True)

        image = Image.new('RGB', (100, 100))
        image_tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(image_tmp_file)
        image_tmp_file.seek(0)

        for i in range(0, settings.POST_MEDIA_MAX_ITEMS):
            user.add_media_to_post(post=draft_post, file=File(image_tmp_file))

        data = {
            'file': image_tmp_file
        }

        url = self._get_url(post=draft_post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_first_media_video_creates_media_thumbnail_and_dimensions(self):
        """
        should create a post media_thumbnail and dimensions when adding the first media video
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user=user)

        for test_video in get_test_videos():
            with open(test_video['path'], 'rb') as file:
                post = user.create_public_post(is_draft=True)

                data = {
                    'file': file
                }

                url = self._get_url(post=post)

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                post.refresh_from_db()

                post_video = post.get_first_media().content_object

                post_video_aspect_ratio = post_video.width / post_video.height
                post_video_thumbnail_aspect_ratio = post_video.thumbnail_width / post_video.thumbnail_height
                post_media_aspect_ratio = post.media_width / post.media_height

                self.assertTrue(post_video_aspect_ratio == post_media_aspect_ratio == post_video_thumbnail_aspect_ratio)

                self.assertIsNotNone(post.media_thumbnail)
                self.assertIsNotNone(post.media_width)
                self.assertIsNotNone(post.media_height)

    def test_add_first_media_image_creates_media_thumbnail_and_dimensions(self):
        """
        should create a post media_thumbnail and dimensions when adding the first media image
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user=user)

        for test_image in get_test_images():
            with open(test_image['path'], 'rb') as file:
                post = user.create_public_post(is_draft=True)

                data = {
                    'file': file
                }

                url = self._get_url(post=post)

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                post.refresh_from_db()

                post_image = post.get_first_media().content_object

                post_image_aspect_ratio = post_image.width / post_image.height
                post_media_aspect_ratio = post.media_width / post.media_height

                self.assertEqual(post_image_aspect_ratio, post_media_aspect_ratio)

                self.assertIsNotNone(post.media_thumbnail)

                self.assertIsNotNone(post.media_thumbnail)
                self.assertIsNotNone(post.media_width)
                self.assertIsNotNone(post.media_height)

    def test_add_media_image_creates_image_thumbnails(self):
        """
        should create an image thumbnail and dimensions when adding a media image
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user=user)

        for test_image in get_test_images():
            with open(test_image['path'], 'rb') as file:
                post = user.create_public_post(is_draft=True)

                data = {
                    'file': file
                }

                url = self._get_url(post=post)

                response = self.client.put(url, data, **headers, format='multipart')

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                post.refresh_from_db()

                first_media = post.get_first_media()
                post_image = first_media.content_object
                self.assertIsNotNone(post_image.thumbnail)

    def test_can_retrieve_post_empty_media_if_no_media(self):
        """
        should be able to retrieve a posts empty media if the pos has no media
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post_text = make_fake_post_text()

        post = user.create_public_post(text=post_text)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertEqual(len(parsed_response), 0)

    def test_can_retrieve_own_post_media_image(self):
        """
        should be able to retrieve an own post media image
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = user.create_public_post(image=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_own_post_media_video(self):
        """
        should be able to retrieve an own post media video
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = user.create_public_post(video=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

        # foreign

    def test_can_retrieve_foreign_user_post_media_image(self):
        """
        should be able to retrieve an foreign_user post media image
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = foreign_user.create_public_post(image=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_foreign_user_post_media_video(self):
        """
        should be able to retrieve an foreign_user post media video
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = foreign_user.create_public_post(video=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_following_user_post_media_image(self):
        """
        should be able to retrieve an following_user post media image
        """
        user = make_user()
        following_user = make_user()

        user.follow_user(user=following_user)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = following_user.create_public_post(image=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_following_user_post_media_video(self):
        """
        should be able to retrieve an following_user post media video
        """
        user = make_user()
        following_user = make_user()

        user.follow_user(user=following_user)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = following_user.create_public_post(video=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_follower_user_post_media_image(self):
        """
        should be able to retrieve an follower_user post media image
        """
        user = make_user()
        follower_user = make_user()

        follower_user.follow_user(user=user)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = follower_user.create_public_post(image=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_follower_user_post_media_video(self):
        """
        should be able to retrieve an follower_user post media video
        """
        user = make_user()
        follower_user = make_user()

        follower_user.follow_user(user=user)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = follower_user.create_public_post(video=file)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_connected_user_post_media_image(self):
        """
        should be able to retrieve an connected_user post media image
        """
        user = make_user()
        connected_user = make_user()
        circle = make_circle(creator=connected_user)

        connected_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=connected_user.pk)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = connected_user.create_encircled_post(image=file, circles_ids=[circle.pk])

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_connected_user_post_media_video(self):
        """
        should be able to retrieve an connected_user post media video
        """
        user = make_user()
        connected_user = make_user()

        circle = make_circle(creator=connected_user)

        connected_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=connected_user.pk)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = connected_user.create_encircled_post(video=file, circles_ids=[circle.pk])

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_cant_retrieve_pending_connection_user_user_encircled_post_media_image(self):
        """
        should not be able to retrieve an pending_connection_user_user encircled post media image
        """
        user = make_user()
        pending_connection_user_user = make_user()

        pending_connection_user_user.connect_with_user_with_id(user_id=user.pk)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            circle = make_circle(creator=pending_connection_user_user)
            post = pending_connection_user_user.create_encircled_post(image=file, circles_ids=[circle.pk])

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_pending_connection_user_user_encircled_post_media_video(self):
        """
        should be able to retrieve an pending_connection_user_user encircled post media video
        """
        user = make_user()
        pending_connection_user_user = make_user()

        pending_connection_user_user.connect_with_user_with_id(user_id=user.pk)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            circle = make_circle(creator=pending_connection_user_user)
            post = pending_connection_user_user.create_encircled_post(video=file, circles_ids=[circle.pk])

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_public_community_post_media_image(self):
        """
        should be able to retrieve an public_community post media image
        """
        user = make_user()
        public_community = make_community()
        community_member = make_user()

        community_member.join_community_with_name(community_name=public_community.name)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = community_member.create_community_post(image=file, community_name=public_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_public_community_post_media_video(self):
        """
        should be able to retrieve an public_community post media video
        """
        user = make_user()
        public_community = make_community()
        community_member = make_user()

        community_member.join_community_with_name(community_name=public_community.name)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = community_member.create_community_post(video=file, community_name=public_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_private_community_part_of_post_media_image(self):
        """
        should be able to retrieve an private_community part of post media image
        """
        user = make_user()
        community_creator = make_user()
        private_community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_creator.invite_user_with_username_to_community_with_name(community_name=private_community.name,
                                                                           username=user.username)
        user.join_community_with_name(community_name=private_community.name)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = community_creator.create_community_post(image=file, community_name=private_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_can_retrieve_private_community_part_of_post_media_video(self):
        """
        should be able to retrieve an private_community part of post media video
        """
        user = make_user()
        community_creator = make_user()
        private_community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        community_creator.invite_user_with_username_to_community_with_name(community_name=private_community.name,
                                                                           username=user.username)
        user.join_community_with_name(community_name=private_community.name)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = community_creator.create_community_post(video=file, community_name=private_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_media = json.loads(response.content)

        post.refresh_from_db()

        post_media = post.get_media().all()

        self._compare_response_media_with_post_media(post_media=post_media, response_media=response_media)

    def test_cannot_retrieve_private_community_not_part_of_post_media_image(self):
        """
        should not be able to retrieve an private_community not part of post media image
        """
        user = make_user()
        community_creator = make_user()
        private_community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        headers = make_authentication_headers_for_user(user=user)

        test_image = get_test_image()

        with open(test_image['path'], 'rb') as file:
            file = File(file)
            post = community_creator.create_community_post(image=file, community_name=private_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_retrieve_private_community_not_part_of_post_media_video(self):
        """
        should not be able to retrieve an private_community not part of post media video
        """
        user = make_user()
        community_creator = make_user()
        private_community = make_community(creator=community_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        headers = make_authentication_headers_for_user(user=user)

        test_video = get_test_video()

        with open(test_video['path'], 'rb') as file:
            file = File(file)
            post = community_creator.create_community_post(video=file, community_name=private_community.name)

        get_worker('high', worker_class=SimpleWorker).work(burst=True)

        url = self._get_url(post=post)

        response = self.client.get(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _compare_response_media_with_post_media(self, response_media, post_media):
        for i in range(0, len(post_media)):
            post_media_item = post_media[i]
            response_item = response_media[i]

            self.assertEqual(post_media_item.id, response_item['id'])
            self.assertEqual(post_media_item.type, response_item['type'])
            self.assertEqual(post_media_item.order, response_item['order'])

            if post_media_item.type == PostMedia.MEDIA_TYPE_IMAGE:
                self.assertEqual(post_media_item.content_object.width, response_item['content_object']['width'])
                self.assertEqual(post_media_item.content_object.height, response_item['content_object']['height'])
                self.assertIn(str(post_media_item.content_object.image), response_item['content_object']['image'])
            elif post_media_item.type == PostMedia.MEDIA_TYPE_VIDEO:
                self.assertEqual(post_media_item.content_object.width, response_item['content_object']['width'])
                self.assertEqual(post_media_item.content_object.height, response_item['content_object']['height'])
                self.assertEqual(post_media_item.content_object.duration, response_item['content_object']['duration'])

                post_media_item_format_set = post_media_item.content_object.format_set.all()

                for j in range(0, len(post_media_item_format_set)):
                    post_media_item_format_set_item = post_media_item_format_set[0]
                    response_post_media_item_format_set_item = response_item['content_object']['format_set'][0]
                    self.assertEqual(post_media_item_format_set_item.format,
                                     response_post_media_item_format_set_item['format'])
                    self.assertEqual(post_media_item_format_set_item.progress,
                                     response_post_media_item_format_set_item['progress'])
                    self.assertIn(str(post_media_item_format_set_item.file),
                                  response_post_media_item_format_set_item['file'])

            else:
                raise Exception('Unsupported media type')

    def _get_url(self, post):
        return reverse('post-media', kwargs={
            'post_uuid': post.uuid
        })
