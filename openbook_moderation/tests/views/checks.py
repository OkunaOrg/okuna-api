from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_global_moderator, make_user, make_moderation_category, \
    make_authentication_headers_for_user
from openbook_moderation.models import ModeratedObject, \
    ModerationCategory, ModerationPenalty

fake = Faker()


class IsNotSuspendedCheckAPITests(OpenbookAPITestCase):
    """
    IsNotSuspendedCheckAPI
    """

    def test_suspension_penalties_prevent_access(self):
        """
        suspension penalties should prevent access to the API
        :return:
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category(severity=ModerationCategory.SEVERITY_MEDIUM)

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        print(response.content)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_expired_suspension_penalty_does_not_prevent_access(self):
        """
        expired suspension penalty should not prevent access to the API
        :return:
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category(severity=ModerationCategory.SEVERITY_MEDIUM)

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        moderation_penalty = ModerationPenalty.objects.get(user_id=user.pk)
        moderation_penalty.expiration = timezone.now()
        moderation_penalty.save()

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_no_suspension_penalties_do_not_prevent_access(self):
        """
        no suspension penalties should not prevent access to the API
        :return:
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category(severity=ModerationCategory.SEVERITY_MEDIUM)

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url()
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def _get_url(self):
        return reverse('is-not-suspended-check')
