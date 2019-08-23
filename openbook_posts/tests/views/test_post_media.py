# Create your tests here.
import json
import tempfile

from PIL import Image
from django.conf import settings
from django.core.files import File
from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
import random

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_user, get_test_videos
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

        self.assertEqual(post_media_image.position, 0)

        post_image = post_media_image.content_object

        self.assertTrue(hasattr(post_image, 'image'))

        self.assertEqual(post_image.width, image_width)
        self.assertEqual(post_image.width, image_width)

        self.assertFalse(hasattr(draft_post, 'image'))

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

                print(post_media_video.position)

                self.assertEqual(post_media_video.position, 0)

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

    def _get_url(self, post):
        return reverse('post-media', kwargs={
            'post_uuid': post.uuid
        })
