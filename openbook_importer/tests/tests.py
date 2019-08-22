from django.urls import reverse
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user
from openbook_common.tests.helpers import make_authentication_headers_for_user


# DISABLED
class UploadFileTests(OpenbookAPITestCase):

    def upload_file_success(self):
        """
        Upload valid archive imports 9 posts, return 200
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/facebook-jaybeenote5.zip',
                  'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        number_of_posts = 9

        response = self.client.get(reverse('posts'), **headers)
        self.assertEqual(len(response.json()), number_of_posts)

    def upload_file_malicious(self):
        """
        the file is malicious, should return 400
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/evil.zip', 'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_file_invalid(self):
        """
        the file is invalid needs to return 400
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/invalid.zip', 'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def upload_file_duplicate(self):
        """
        Uploading duplicate archive, should skip all imported posts
        and return 200.
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/facebook-jaybeenote5.zip',
                  'rb') as fd:
            for i in range(0, 2):
                response = self.client.post(reverse('uploads'), {'file': fd},
                                            **headers)
                fd.seek(0)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        number_of_posts = 9

        response = self.client.get(reverse('posts'), **headers)
        self.assertEqual(len(response.json()), number_of_posts)
