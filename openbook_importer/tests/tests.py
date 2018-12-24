from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user


class UploadFileTests(APITestCase):

    def test_upload_file_success(self):
        """
        Upload valid archive should return 200
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/facebook-jaybeenote5.zip', 'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd}, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_file_malicious(self):
        """
        should return a 400 when the file is malicious (unkown file magic)
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/evil.zip', 'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_file_invalid(self):
        """
        should return a 400 when the file is invalid
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/invalid.zip', 'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd}, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
