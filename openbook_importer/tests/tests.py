from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_common.tests.helpers import make_user
from openbook_importer.models import ImportedPost, Import, ImportedFriend
from openbook_common.tests.helpers import make_authentication_headers_for_user


class UploadFileTests(APITestCase):

    def test_upload_file_success(self):
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

    def test_upload_file_malicious(self):
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

    def test_upload_file_duplicate(self):
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

    def test_postimport_entries(self):
        """
        Uploading archive test ImportedPost table should contain 9 entries
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

        number_of_entries = 9

        self.assertEqual(len(ImportedPost.objects.all()), number_of_entries)

    def test_import_entries(self):
        """
        Uploading archive Import table should contain 1 zip entry
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

        number_of_entries = 1

        self.assertEqual(len(Import.objects.all()), number_of_entries)

    def test_friendimport_entries(self):
        """
        Uploading archive Friend table should contain 2 zip entries
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

        number_of_entries = 2

        self.assertEqual(len(ImportedFriend.objects.all()), number_of_entries)

    def test_findfriend_entries(self):
        """
        Uploading athe archive as a new user, would lead to a connection
        between user1 and user2
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/facebook-jaybeenote5.zip',
                  'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        user2 = make_user()
        headers = make_authentication_headers_for_user(user2)

        with open('openbook_importer/tests/facebook-jayjay6.zip',
                  'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        number_of_entries = 2

        friend_objects = ImportedFriend.objects.all()
        self.assertEqual(len(friend_objects), number_of_entries)

        for friend_object in friend_objects:
            self.assertTrue(friend_object.user1_id == 1)
            self.assertTrue(friend_object.user2_id == 2)

    def test_delete_importedposts(self):
        """
        Deleting a previously imported import, should remove all corresponding posts.
        """

        user = make_user()
        headers = make_authentication_headers_for_user(user)

        with open('openbook_importer/tests/facebook-jayjay6.zip',
                  'rb') as fd:
            response = self.client.post(reverse('uploads'), {'file': fd},
                                        **headers)

        user.imports.filter(id=1).delete()

        self.assertEqual(user.imports.all().count(), 0)
        self.assertEqual(len(ImportedPost.objects.all()), 0)
