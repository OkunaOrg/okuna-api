# Create your tests here.


from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_auth.models import User


class RegistrationAPITests(APITestCase):
    """
    RegistrationAPI
    """

    def test_username_is_required(self):
        """
        should require a username
        """
        pass

    def test_name_is_required(self):
        """
        should require a name
        """
        pass

    def test_email_is_required(self):
        """
        should require an email
        """
        pass

    def test_birth_date_is_required(self):
        """
        should require a birth_date
        """
        pass

    def test_avatar_is_optional(self):
        """
        should NOT require an avatar
        """
        pass

    def test_username_is_not_taken(self):
        """
        should check whether the username is not taken
        """
        pass

    def test_email_is_not_taken(self):
        """
        should check whether the email is not taken
        """
        pass

    def test_user_is_created(self):
        """
        should create a User model instance
        """
        pass

    def test_user_profile_is_created(self):
        """
        should create a UserProfile model instance linked to the User model instance
        """
        pass
