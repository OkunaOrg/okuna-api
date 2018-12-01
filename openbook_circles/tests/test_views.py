# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from mixer.backend.django import mixer

from openbook_auth.models import User
from faker import Faker

import logging
import json

from openbook_circles.models import Circle

logger = logging.getLogger(__name__)

fake = Faker()


class CirclesAPITests(APITestCase):
    """
    CirclesAPI
    """

    def test_create_circle(self):
        """
        should be able to create a circle and return 201
        """
        user = mixer.blend(User)

        auth_token = user.auth_token.key

        circle_name = fake.name()
        circle_color = fake.hex_color()

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        data = {
            'name': circle_name,
            'color': circle_color
        }

        url = self._get_url()

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Circle.objects.filter(name=circle_name, color=circle_color, creator_id=user.pk).count() == 1)

    def test_retrieve_own_circles(self):
        """
        should retrieve the all own circles and return 200
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key
        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circles = mixer.cycle(5).blend(Circle, creator=user)
        circles_ids = [circle.pk for circle in circles]

        # We also expect to get back the default circles
        circles_ids.append(user.connections_circle_id)

        url = self._get_url()
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_circles = json.loads(response.content)

        self.assertEqual(len(response_circles), len(circles_ids))

        for response_circle in response_circles:
            response_circle_id = response_circle.get('id')
            self.assertIn(response_circle_id, circles_ids)

    def _get_url(self):
        return reverse('circles')


class CircleItemAPITests(APITransactionTestCase):
    """
    CircleItemAPI
    """
    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_delete_own_circle(self):
        """
        should be able to delete an own circle and return 200
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle = mixer.blend(Circle, creator=user)
        circle_id = circle.pk

        url = self._get_url(circle_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Circle.objects.filter(id=circle_id).count() == 0)

    def test_cannot_delete_world_circle(self):
        """
        should not be able to own world circle and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle_id = Circle.get_world_circle_id()

        url = self._get_url(circle_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(id=circle_id).count() == 1)

    def test_cannot_delete_connections_circle(self):
        """
        should not be able to delete own connections circle and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle_id = user.connections_circle_id

        url = self._get_url(circle_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(id=circle_id).count() == 1)

    def test_cannot_delete_other_user_circle(self):
        """
        should not be able to delete another user's circle and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        other_user = mixer.blend(User)

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle = mixer.blend(Circle, creator=other_user)
        circle_id = circle.pk

        url = self._get_url(circle_id)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(id=circle_id).count() == 1)

    def test_can_update_own_circle(self):
        """
        should be able to update own circle and return 200
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle_color = fake.hex_color()
        circle = mixer.blend(Circle, creator=user, color=circle_color)
        circle_id = circle.pk

        new_circle_name = fake.name()
        new_circle_color = fake.hex_color()

        data = {
            'name': new_circle_name,
            'color': new_circle_color
        }

        url = self._get_url(circle_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Circle.objects.filter(name=new_circle_name, id=circle_id, color=new_circle_color).count() == 1)

    def test_cannot_update_other_user_circle(self):
        """
        should not be able to update the circle of another user and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        another_user = mixer.blend(User)

        circle_color = fake.hex_color()
        circle = mixer.blend(Circle, creator=another_user, color=circle_color)
        circle_id = circle.pk

        new_circle_name = fake.name()
        new_circle_color = fake.hex_color()

        data = {
            'name': new_circle_name,
            'color': new_circle_color
        }

        url = self._get_url(circle_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(name=new_circle_name, id=circle_id, color=new_circle_color).count() == 0)

    def test_cannot_update_world_circle(self):
        """
        should not be able to update own world circle and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle_id = Circle.get_world_circle_id()

        new_circle_name = fake.name()
        new_circle_color = fake.hex_color()

        data = {
            'name': new_circle_name,
            'color': new_circle_color
        }

        url = self._get_url(circle_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(name=new_circle_name, id=circle_id, color=new_circle_color).count() == 0)

    def test_cannot_update_connections_circle(self):
        """
        should not be able to update own connections circle and return 400
        """
        user = mixer.blend(User)
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        circle_id = user.connections_circle_id

        new_circle_name = fake.name()
        new_circle_color = fake.hex_color()

        data = {
            'name': new_circle_name,
            'color': new_circle_color
        }

        url = self._get_url(circle_id)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Circle.objects.filter(name=new_circle_name, id=circle_id, color=new_circle_color).count() == 0)

    def _get_url(self, circle_id):
        return reverse('circle', kwargs={
            'circle_id': circle_id
        })
