import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_notification, \
    make_fake_post_text, make_moderation_category, make_moderation_report_description, make_circle, make_community
from openbook_communities.models import Community
from openbook_moderation.models import ModerationReport, ModeratedObject
from openbook_notifications.models import Notification

fake = Faker()


class ReportPostAPITests(APITestCase):
    """
    ReportPostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_report_public_post(self):
        """
        should be able to report a post with a description and return 201
        """
        post_creator = make_user()
        post_text = make_fake_post_text()
        post = post_creator.create_public_post(text=post_text)

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                        moderated_object__object_id=post.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_can_report_encircled_post_part_of(self):
        """
        should be able to report an encircled post part of with a description and return 201
        """
        post_creator = make_user()

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        circle = make_circle(creator=post_creator)

        post_creator.connect_with_user_with_id(user_id=post_reporter.pk, circles_ids=[circle.pk])
        post_reporter.confirm_connection_with_user_with_id(user_id=post_creator.pk)

        post_text = make_fake_post_text()
        post = post_creator.create_encircled_post(text=post_text, circles_ids=[circle.pk])

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                        moderated_object__object_id=post.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_cant_report_encircled_post(self):
        """
        should not be able to report an encircled post with a description and return 400
        """
        post_creator = make_user()

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        circle = make_circle(creator=post_creator)

        post_text = make_fake_post_text()
        post = post_creator.create_encircled_post(text=post_text, circles_ids=[circle.pk])

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                         moderated_object__object_id=post.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_can_report_public_community_post(self):
        """
        should be able to report an public community post with a description and return 201
        """
        post_creator = make_user()

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        community = make_community(creator=post_creator)

        post_text = make_fake_post_text()
        post = post_creator.create_community_post(text=post_text, community_name=community.name)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                        moderated_object__object_id=post.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_can_report_private_community_part_of_post(self):
        """
        should be able to report a private community part of, post with a description and return 201
        """
        post_creator = make_user()

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        community = make_community(creator=post_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_text = make_fake_post_text()
        post = post_creator.create_community_post(text=post_text, community_name=community.name)

        post_creator.invite_user_with_username_to_community_with_name(username=post_reporter.username,
                                                                      community_name=community.name)
        post_reporter.join_community_with_name(community_name=community.name)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                        moderated_object__object_id=post.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_cant_report_private_community_post(self):
        """
        should not be able to report a private community post with a description and return 400
        """
        post_creator = make_user()

        post_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        community = make_community(creator=post_creator, type=Community.COMMUNITY_TYPE_PRIVATE)

        post_text = make_fake_post_text()
        post = post_creator.create_community_post(text=post_text, community_name=community.name)

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                         moderated_object__object_id=post.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_cant_report_post_without_category(self):
        """
        should not be able to report a post without a category and return 400
        """
        post_creator = make_user()
        post_text = make_fake_post_text()
        post = post_creator.create_public_post(text=post_text)

        post_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                         moderated_object__object_id=post.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                         description=report_description
                                                         ).exists())

    def test_cant_report_post_twice(self):
        """
        should not be able to report a post twice and return 400
        """
        post_creator = make_user()
        post_text = make_fake_post_text()
        post = post_creator.create_public_post(text=post_text)

        report_category = make_moderation_category()
        post_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        self.client.post(url, data={
            'description': report_description,
            'category_id': report_category.pk
        }, **headers)

        response = self.client.post(url, data={
            'description': report_description,
            'category_id': report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertEqual(1, ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                            moderated_object__object_id=post.pk,
                                                            moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                            description=report_description
                                                            ).count())

    def test_can_report_post_without_description(self):
        """
        should be able to report a post without a description and return 201
        """
        post_creator = make_user()
        post_text = make_fake_post_text()
        post = post_creator.create_public_post(text=post_text)

        post_reporter = make_user()
        report_category = make_moderation_category()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_reporter.has_reported_post_with_id(post_id=post.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_reporter.pk,
                                                        moderated_object__object_id=post.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                        category_id=report_category.pk
                                                        ).exists())

    def _get_url(self, post):
        return reverse('report-post', kwargs={
            'post_uuid': post.uuid
        })
