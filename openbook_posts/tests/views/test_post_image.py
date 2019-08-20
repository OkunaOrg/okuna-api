# Create your tests here.
import json
import tempfile

from PIL import Image
from django.core.files.images import ImageFile
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_user

logger = logging.getLogger(__name__)
fake = Faker()


class PostImageAPITests(APITestCase):
    """
    PostImageAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_set_image_to_draft_post(self):
        """
        should be able to set an image to a draft post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        draft_post = user.create_public_post(is_draft=True)

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'image': tmp_file
        }

        url = self._get_url(post=draft_post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        draft_post.refresh_from_db()

        self.assertIsNotNone(draft_post.image)

    def test_cant_set_image_to_published_post(self):
        """
        should not be able to set an image to a published post
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post = user.create_public_post(text=make_fake_post_text())

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'image': tmp_file
        }

        url = self._get_url(post=post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(hasattr(post, 'image'))

    def test_cannot_set_image_to_draft_with_existing_image(self):
        """
        should not be able to set an image to a draft post with an existing image
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        initial_image = Image.new('RGB', (100, 100))
        initial_image_tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        initial_image.save(initial_image_tmp_file)
        initial_image_tmp_file.seek(0)

        draft_post = user.create_public_post(is_draft=True, image=ImageFile(initial_image_tmp_file))

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)

        data = {
            'image': tmp_file
        }

        url = self._get_url(post=draft_post)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post):
        return reverse('post-image', kwargs={
            'post_uuid': post.uuid
        })
