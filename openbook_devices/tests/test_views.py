import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_device
from openbook_devices.models import Device

fake = Faker()


class DevicesAPITests(OpenbookAPITestCase):
    """
    DevicesAPI
    """

    def test_can_create_device_without_optional_arguments(self):
        """
        should be able to create a new device and return 200
        """

        user = make_user()
        device_uuid = fake.uuid4()

        request_body = {
            'uuid': device_uuid,
        }

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, request_body, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Device.objects.filter(uuid=device_uuid, owner=user).exists())

    def test_can_create_device_with_all_arguments(self):
        """
        should be able to create a new device and return 200
        """

        user = make_user()
        device_uuid = fake.uuid4()
        device_name = fake.user_name()

        request_body = {
            'uuid': device_uuid,
            'name': device_name,
        }

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.put(url, request_body, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            Device.objects.filter(uuid=device_uuid, owner=user).exists())

    def test_can_retrieve_devices(self):
        """
        should be able to retrieve all devices and return 200
        """
        user = make_user()

        amount_of_devices = 5
        devices_ids = []

        for i in range(0, amount_of_devices):
            device = make_device(owner=user)
            devices_ids.append(str(device.uuid))

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_devices = json.loads(response.content)

        self.assertEqual(len(response_devices), len(devices_ids))

        for response_device in response_devices:
            response_device_uuid = response_device.get('uuid')
            self.assertIn(response_device_uuid, devices_ids)

    def test_can_delete_devices(self):
        """
        should be able to delete all devices and return 200
        """
        user = make_user()

        amount_of_devices = 5
        devices_ids = []

        for i in range(0, amount_of_devices):
            device = make_device(owner=user)
            devices_ids.append(device.uuid)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Device.objects.filter(owner=user).exists())

    def _get_url(self):
        return reverse('devices')


class DeviceItemAPITests(OpenbookAPITestCase):
    """
    DeviceItemAPI
    """

    def test_can_retrieve_own_device(self):
        """
        should be able to retrieve an own device
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        device = make_device(owner=user)
        device_uuid = device.uuid

        url = self._get_url(device_uuid)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_device = json.loads(response.content)

        self.assertEqual(response_device['uuid'], str(device.uuid))

    def test_cant_retrieve_foreign_device(self):
        """
        should not be able to retrieve a foreign device
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        device = make_device(owner=foreign_user)
        device_uuid = device.uuid

        url = self._get_url(device_uuid)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_delete_own_device(self):
        """
        should be able to delete an own device and return 200
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user)

        device = make_device(owner=user)
        device_uuid = device.uuid

        url = self._get_url(device_uuid)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Device.objects.filter(uuid=device_uuid).exists())

    def test_cannot_delete_foreign_device(self):
        """
        should not be able to delete a foreign device and return 404
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        device = make_device(owner=foreign_user)
        device_uuid = device.uuid

        url = self._get_url(device_uuid)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Device.objects.filter(uuid=device_uuid).exists())

    def test_can_update_a_device_name(self):
        """
        should be able to update a device name and return 200
        """

        user = make_user()
        device = make_device(owner=user)

        new_device_name = fake.user_name()

        request_body = {
            'name': new_device_name
        }

        url = self._get_url(device_uuid=device.uuid)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, request_body, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(Device.objects.filter(uuid=device.uuid, name=new_device_name).exists())

    def test_can_update_a_device_updatable_arguments_at_once(self):
        """
        should be able to update a device updatable_arguments at once and return 200
        """

        user = make_user()
        device = make_device(owner=user)

        new_name = fake.user_name()

        request_body = {
            'name': new_name,
        }

        url = self._get_url(device_uuid=device.uuid)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, request_body, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(
            Device.objects.filter(uuid=device.uuid,
                                  name=new_name, ).exists())

    def test_cant_update_a_foreign_device(self):
        """
        should not be able to update a foreign device and return 403
        """

        user = make_user()
        foreign_user = make_user()
        device = make_device(owner=foreign_user)

        new_name = fake.user_name()

        request_body = {
            'name': new_name,
        }

        url = self._get_url(device_uuid=device.uuid)
        headers = make_authentication_headers_for_user(user)
        response = self.client.patch(url, request_body, **headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertFalse(
            Device.objects.filter(uuid=device.uuid,
                                  name=new_name, ).exists())

    def _get_url(self, device_uuid):
        return reverse('device', kwargs={
            'device_uuid': device_uuid
        })
