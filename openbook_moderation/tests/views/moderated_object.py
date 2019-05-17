import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

fake = Faker()


class ModeratedObjectAPITests(APITestCase):
    """
    ModeratedObjectAPI
    """

    def test_can_update_user_moderated_object_if_openbook_staff(self):
        """
        should be able to update a user moderated object openbook staff
        """
        pass

    def test_cant_update_user_moderated_object_if_not_openbook_staff(self):
        """
        should not be able to update a user moderated object if not openbook staff
        """
        pass

    def test_cant_update_user_moderated_object_if_community_staff(self):
        """
        should not be able to update a user moderated object if community staff
        """
        pass

    def test_can_update_community_moderated_object_if_openbook_staff(self):
        """
        should be able to update a community moderated object openbook staff
        """
        pass

    def test_cant_update_community_moderated_object_if_not_openbook_staff(self):
        """
        should not be able to update a community moderated object if not openbook staff
        """
        pass

    def test_cant_update_community_moderated_object_if_community_staff(self):
        """
        should not be able to update a community moderated object if community staff
        """
        pass

    def test_can_update_community_post_moderated_object_if_openbook_staff(self):
        """
        should be able to update a community post moderated object openbook staff
        """
        pass

    def test_can_update_community_post_comment_moderated_object_if_openbook_staff(self):
        """
        should be able to update a community post comment moderated object openbook staff
        """
        pass

    def test_cant_update_community_post_moderated_object_if_not_openbook_staff(self):
        """
        should not be able to update a community post moderated object if not openbook staff
        """
        pass

    def test_cant_update_community_post_comment_moderated_object_if_not_openbook_staff(self):
        """
        should not be able to update a community post comment moderated object if not openbook staff
        """
        pass

    def test_can_update_community_post_moderated_object_if_community_staff(self):
        """
        should be able to update a community post moderated object if community staff
        """
        pass

    def test_can_update_community_post_comment_moderated_object_if_community_staff(self):
        """
        should be able to update a community post comment moderated object if community staff
        """
        pass

    def test_cant_update_community_post_moderated_object_if_not_openbook_staff_or_community_staff(self):
        """
        should not be able to update a community post moderated object if not openbook staff or community staff
        """
        pass

    def test_cant_update_community_post_comment_moderated_object_if_not_openbook_staff_or_community_staff(self):
        """
        should not be able to update a community post comment moderated object if not openbook staff or community staff
        """
        pass

    def _get_url(self):
        return reverse('moderated-object')
