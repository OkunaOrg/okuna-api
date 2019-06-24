from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import json
from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_fake_post_text


class TranslateTextAPITests(APITestCase):
    """
    TranslateTextAPI
    These tests are for translation using AWS Translate
    """

    fixtures = [
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_translate_text(self):
        """
        should be able to translate text using aws translate and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        text = 'Ik ben en man 😀. Jij bent en vrouw.'

        url = self._get_url()

        response = self.client.post(url, {
            'text': text,
            'source_language_code': 'nl',
            'target_language_code': 'en'
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['translated_text'], 'I am a man 😀. You\'re a woman.')

    def test_return_error_between_unsupported_translate_pairs(self):
        """
        should return error using aws translate when translating between unsupported pairs (Norwegian to arabic) and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        text = make_fake_post_text()

        url = self._get_url()

        response = self.client.post(url, {
            'text': text,
            'source_language_code': 'no',  # norwegian
            'target_language_code': 'ar'  # arabic
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_when_text_length_exceeds_max_setting(self):
        """
        should return appropriate error when length of text is more than maximum in settings.py return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        text = 'Ik ben en man 😀. Jij bent en vrouw. Dit is en tekst van meer dan viertig characters.'

        url = self._get_url()
        response = self.client.post(url, {
            'text': text,
            'source_language_code': 'nl',
            'target_language_code': 'en'
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self):
        return reverse('translate-text')

