# Create your tests here.
from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase
from mixer.backend.django import mixer

from openbook_auth.models import User
from faker import Faker

import logging
import json

from openbook_circles.models import Circle
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_fake_circle_name

logger = logging.getLogger(__name__)

fake = Faker()


class CirclesAPITests(OpenbookAPITestCase):
    """
    CirclesAPI
    """

    def test_create_circle(self):
        """
        should be able to create a circle and return 201
        """
        user = make_user()

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
        user = make_user()
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


class CircleItemAPITests(OpenbookAPITestCase):
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
        user = make_user()
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
        user = make_user()
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
        user = make_user()
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
        user = make_user()
        auth_token = user.auth_token.key

        other_user = make_user()

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
        user = make_user()
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

    def test_can_update_own_circle_users(self):
        """
        should be able to update an own circle and return 200
        """
        user = make_user()

        circle = mixer.blend(Circle, creator=user)
        circle_id = circle.pk

        users_to_connect_with_in_circle = 4

        for i in range(users_to_connect_with_in_circle):
            user_to_connect_with = make_user()
            user.connect_with_user_with_id(user_to_connect_with.pk, circles_ids=[circle_id])

        new_users_to_connect_with_in_circle_amount = 2
        new_users_to_connect_with_in_circle = []
        new_users_to_connect_with_in_circle_usernames = []

        for i in range(new_users_to_connect_with_in_circle_amount):
            user_to_connect_with = make_user()
            new_users_to_connect_with_in_circle.append(user_to_connect_with)
            new_users_to_connect_with_in_circle_usernames.append(user_to_connect_with.username)

        data = {
            'usernames': ','.join(map(str, new_users_to_connect_with_in_circle_usernames))
        }

        url = self._get_url(circle_id)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for new_user_to_connect_with in new_users_to_connect_with_in_circle:
            self.assertTrue(
                user.is_connected_with_user_with_id_in_circle_with_id(new_user_to_connect_with.pk, circle_id))

    def test_can_update_own_circle_users_to_none(self):
        """
        should be able to update an own circle and return 200
        """
        user = make_user()

        circle = mixer.blend(Circle, creator=user)
        circle_id = circle.pk

        users_to_connect_with_in_circle = 4

        for i in range(users_to_connect_with_in_circle):
            user_to_connect_with = make_user()
            user.connect_with_user_with_id(user_to_connect_with.pk, circles_ids=[circle_id])

        data = {
            'usernames': ''
        }

        url = self._get_url(circle_id)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        circle.refresh_from_db()

        self.assertEqual(len(circle.users), 0)

    def test_cannot_update_other_user_circle(self):
        """
        should not be able to update the circle of another user and return 400
        """
        user = make_user()
        auth_token = user.auth_token.key

        headers = {'HTTP_AUTHORIZATION': 'Token %s' % auth_token}

        another_user = make_user()

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
        user = make_user()
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
        user = make_user()
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


class CircleNameCheckAPITests(OpenbookAPITestCase):
    """
    CircleNameCheckAPI
    """

    def test_circle_name_not_taken(self):
        """
        should return status 202 if circle name is not taken.
        """

        user = make_user()

        circle_name = make_fake_circle_name()
        request_data = {'name': circle_name}

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, request_data, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_circle_name_taken(self):
        """
        should return status 400 if the circleName is taken
        """
        user = make_user()
        color = fake.hex_color()

        circle = user.create_circle(name=make_fake_circle_name(), color=color)

        request_data = {'name': circle.name}

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(url, request_data, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('circle-name-check')
