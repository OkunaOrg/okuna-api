import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from openbook_common.tests.models import OpenbookAPITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, make_notification, \
    make_fake_post_text, make_moderation_category, make_moderation_report_description, make_circle, make_community, \
    make_fake_post_comment_text, make_hashtag
from openbook_communities.models import Community
from openbook_moderation.models import ModerationReport, ModeratedObject

fake = Faker()


class ReportPostAPITests(OpenbookAPITestCase):
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

    def test_reporting_post_should_not_add_community_to_moderated(self):
        """
        reporting a post should not add a community to it
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

        self.assertTrue(ModeratedObject.objects.filter(object_id=post.pk,
                                                       object_type=ModeratedObject.OBJECT_TYPE_POST,
                                                       community__isnull=True
                                                       ).exists())

    def test_cant_report_own_post(self):
        """
        should not be able to report an own post and return 400
        """
        post_creator = make_user()
        post_text = make_fake_post_text()
        post = post_creator.create_public_post(text=post_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(post_creator)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_creator.has_reported_post_with_id(post_id=post.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_creator.pk,
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

    def test_reporting_community_post_adds_it_to_moderated_object(self):
        """
        reporting a community post should add the post community to the moderated object community
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

        self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=post.pk,
            object_type=ModeratedObject.OBJECT_TYPE_POST,
            category_id=report_category.pk,
            community_id=community.pk
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


class ReportPostCommentAPITests(OpenbookAPITestCase):
    """
    ReportPostCommentAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_report_public_post_comment(self):
        """
        should be able to report a post_comment with a description and return 201
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                        moderated_object__object_id=post_comment.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_reporting_post_comment_should_not_add_community_to_moderated(self):
        """
        reporting a post comment should not add a community to the moderated object
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=post_comment.pk,
            object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
        ).exists())

    def test_cant_report_own_post_comment(self):
        """
        should not be able to report an own post_comment and return 400
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_creator)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_comment_creator.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_comment_creator.pk,
                                                         moderated_object__object_id=post_comment.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_can_report_encircled_post_comment_part_of(self):
        """
        should be able to report an encircled post_comment part of with a description and return 201
        """
        post_comment_creator = make_user()
        post_comment_reporter = make_user()

        circle = make_circle(creator=post_comment_creator)
        post_comment_creator.connect_with_user_with_id(user_id=post_comment_reporter.pk, circles_ids=[circle.pk])
        post_comment_reporter.confirm_connection_with_user_with_id(user_id=post_comment_creator.pk)

        post = post_comment_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                        moderated_object__object_id=post_comment.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_cant_report_encircled_post_comment(self):
        """
        should not be able to report an encircled post_comment with a description and return 400
        """
        post_comment_creator = make_user()
        post_comment_reporter = make_user()

        circle = make_circle(creator=post_comment_creator)

        post = post_comment_creator.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                         moderated_object__object_id=post_comment.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_can_report_public_community_post_comment(self):
        """
        should be able to report an public community post_comment with a description and return 201
        """
        post_comment_creator = make_user()
        community = make_community(creator=post_comment_creator)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                        moderated_object__object_id=post_comment.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_can_report_private_community_part_of_post_comment(self):
        """
        should be able to report a private community part of, post_comment with a description and return 201
        """
        post_comment_creator = make_user()
        post_comment_reporter = make_user()

        community = make_community(creator=post_comment_creator, type=Community.COMMUNITY_TYPE_PRIVATE)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment_creator.invite_user_with_username_to_community_with_name(username=post_comment_reporter.username,
                                                                              community_name=community.name)
        post_comment_reporter.join_community_with_name(community_name=community.name)

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                        moderated_object__object_id=post_comment.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_cant_report_private_community_post_comment(self):
        """
        should not be able to report a private community post_comment with a description and return 400
        """
        post_comment_creator = make_user()
        post_comment_reporter = make_user()

        community = make_community(creator=post_comment_creator, type=Community.COMMUNITY_TYPE_PRIVATE)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                         moderated_object__object_id=post_comment.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_reporting_community_post_comment_adds_it_to_the_moderated_object(self):
        """
        reporting a community post comment should add the comment community to the moderated object
        """
        post_comment_creator = make_user()
        community = make_community(creator=post_comment_creator)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModeratedObject.objects.filter(
            object_id=post_comment.pk,
            object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
        ).exists())

    def test_cant_report_post_comment_without_category(self):
        """
        should not be able to report a post_comment without a category and return 400
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                         moderated_object__object_id=post_comment.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                         description=report_description,
                                                         ).exists())

    def test_cant_report_post_comment_twice(self):
        """
        should not be able to report a post_comment twice and return 400
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertEqual(1, ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                            moderated_object__object_id=post_comment.pk,
                                                            moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                            description=report_description
                                                            ).count())

    def test_can_report_post_comment_without_description(self):
        """
        should be able to report a post_comment without a description and return 201
        """
        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())

        post_comment_text = make_fake_post_comment_text()
        post_comment = post_comment_creator.comment_post_with_id(post_id=post.pk, text=post_comment_text)

        post_comment_reporter = make_user()
        report_category = make_moderation_category()

        url = self._get_url(post_comment=post_comment, post=post)
        headers = make_authentication_headers_for_user(post_comment_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(post_comment_reporter.has_reported_post_comment_with_id(post_comment_id=post_comment.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=post_comment_reporter.pk,
                                                        moderated_object__object_id=post_comment.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_POST_COMMENT,
                                                        category_id=report_category.pk
                                                        ).exists())

    def _get_url(self, post, post_comment):
        return reverse('report-post-comment', kwargs={
            'post_comment_id': post_comment.pk,
            'post_uuid': str(post.uuid)
        })


class ReportUserAPITests(OpenbookAPITestCase):
    """
    ReportUserAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_report_user(self):
        """
        should be able to report a user with a description and return 201
        """
        user = make_user()

        user_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_reporter.has_reported_user_with_id(user_id=user.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=user_reporter.pk,
                                                        moderated_object__object_id=user.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_reporting_user_should_not_add_community_to_moderated(self):
        """
        reporting a user should not add a community to it
        """
        user = make_user()

        user_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(ModeratedObject.objects.filter(object_id=user.pk,
                                                       object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                       community__isnull=True
                                                       ).exists())

    def test_cant_report_oneself(self):
        """
        should not be able to report oneself and return 400
        """
        user = make_user()

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_reported_user_with_id(user_id=user.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=user.pk,
                                                         moderated_object__object_id=user.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_cant_report_user_without_category(self):
        """
        should not be able to report a user without a category and return 400
        """
        user = make_user()

        user_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user_reporter)

        response = self.client.post(url, data={
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user_reporter.has_reported_user_with_id(user_id=user.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=user_reporter.pk,
                                                         moderated_object__object_id=user.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                         description=report_description,
                                                         ).exists())

    def test_cant_report_user_twice(self):
        """
        should not be able to report a user twice and return 400
        """
        user = make_user()

        user_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user_reporter)

        self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user_reporter.has_reported_user_with_id(user_id=user.pk))
        self.assertEqual(1, ModerationReport.objects.filter(reporter_id=user_reporter.pk,
                                                            moderated_object__object_id=user.pk,
                                                            moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                            description=report_description,
                                                            category_id=report_category.pk
                                                            ).count())

    def test_can_report_user_without_description(self):
        """
        should be able to report a user without a description and return 201
        """
        user = make_user()

        user_reporter = make_user()
        report_category = make_moderation_category()

        url = self._get_url(user)
        headers = make_authentication_headers_for_user(user_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user_reporter.has_reported_user_with_id(user_id=user.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=user_reporter.pk,
                                                        moderated_object__object_id=user.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_USER,
                                                        category_id=report_category.pk
                                                        ).exists())

    def _get_url(self, user):
        return reverse('report-user', kwargs={
            'user_username': user.username
        })


class ReportCommunityAPITests(OpenbookAPITestCase):
    """
    ReportCommunityAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_report_community(self):
        """
        should be able to report a community with a description and return 201
        """
        community_owner = make_user()
        community = make_community(creator=community_owner)

        community_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(community_reporter.has_reported_community_with_id(community_id=community.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=community_reporter.pk,
                                                        moderated_object__object_id=community.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_reporting_community_should_not_add_community_to_moderated(self):
        """
        reporting a community should not add a community to it
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(ModeratedObject.objects.filter(object_id=community.pk,
                                                       object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                       community__isnull=True
                                                       ).exists())

    def test_cant_report_own_community(self):
        """
        should not be able to report own and return 400
        """
        community_owner = make_user()
        community = make_community(creator=community_owner)

        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_owner)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(community_owner.has_reported_community_with_id(community_id=community.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=community_owner.pk,
                                                         moderated_object__object_id=community.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                         description=report_description,
                                                         category_id=report_category.pk
                                                         ).exists())

    def test_cant_report_community_without_category(self):
        """
        should not be able to report a community without a category and return 400
        """
        community_owner = make_user()
        community = make_community(creator=community_owner)

        community_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_reporter)

        response = self.client.post(url, data={
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(community_reporter.has_reported_community_with_id(community_id=community.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=community_reporter.pk,
                                                         moderated_object__object_id=community.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                         description=report_description,
                                                         ).exists())

    def test_cant_report_community_twice(self):
        """
        should not be able to report a community twice and return 400
        """
        community_owner = make_user()
        community = make_community(creator=community_owner)

        community_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_reporter)

        self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(community_reporter.has_reported_community_with_id(community_id=community.pk))
        self.assertEqual(1, ModerationReport.objects.filter(reporter_id=community_reporter.pk,
                                                            moderated_object__object_id=community.pk,
                                                            moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                            description=report_description,
                                                            category_id=report_category.pk
                                                            ).count())

    def test_can_report_community_without_description(self):
        """
        should be able to report a community without a description and return 201
        """
        community_owner = make_user()
        community = make_community(creator=community_owner)

        community_reporter = make_user()
        report_category = make_moderation_category()

        url = self._get_url(community)
        headers = make_authentication_headers_for_user(community_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(community_reporter.has_reported_community_with_id(community_id=community.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=community_reporter.pk,
                                                        moderated_object__object_id=community.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_COMMUNITY,
                                                        category_id=report_category.pk
                                                        ).exists())

    def _get_url(self, community):
        return reverse('report-community', kwargs={
            'community_name': community.name
        })


class ReportHashtagAPITests(OpenbookAPITestCase):
    """
    ReportHashtagAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_can_report_hashtag(self):
        """
        should be able to report a hashtag with a description and return 201
        """
        hashtag = make_hashtag()

        hashtag_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(hashtag)
        headers = make_authentication_headers_for_user(hashtag_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(hashtag_reporter.has_reported_hashtag_with_id(hashtag_id=hashtag.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=hashtag_reporter.pk,
                                                        moderated_object__object_id=hashtag.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_HASHTAG,
                                                        description=report_description,
                                                        category_id=report_category.pk
                                                        ).exists())

    def test_cant_report_hashtag_without_category(self):
        """
        should not be able to report a hashtag without a category and return 400
        """
        hashtag = make_hashtag()

        hashtag_reporter = make_user()
        report_description = make_moderation_report_description()

        url = self._get_url(hashtag)
        headers = make_authentication_headers_for_user(hashtag_reporter)

        response = self.client.post(url, data={
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(hashtag_reporter.has_reported_hashtag_with_id(hashtag_id=hashtag.pk))
        self.assertFalse(ModerationReport.objects.filter(reporter_id=hashtag_reporter.pk,
                                                         moderated_object__object_id=hashtag.pk,
                                                         moderated_object__object_type=ModeratedObject.OBJECT_TYPE_HASHTAG,
                                                         description=report_description,
                                                         ).exists())

    def test_cant_report_hashtag_twice(self):
        """
        should not be able to report a hashtag twice and return 400
        """
        hashtag = make_hashtag()

        hashtag_reporter = make_user()
        report_category = make_moderation_category()
        report_description = make_moderation_report_description()

        url = self._get_url(hashtag)
        headers = make_authentication_headers_for_user(hashtag_reporter)

        self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
            'description': report_description
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(hashtag_reporter.has_reported_hashtag_with_id(hashtag_id=hashtag.pk))
        self.assertEqual(1, ModerationReport.objects.filter(reporter_id=hashtag_reporter.pk,
                                                            moderated_object__object_id=hashtag.pk,
                                                            moderated_object__object_type=ModeratedObject.OBJECT_TYPE_HASHTAG,
                                                            description=report_description,
                                                            category_id=report_category.pk
                                                            ).count())

    def test_can_report_hashtag_without_description(self):
        """
        should be able to report a hashtag without a description and return 201
        """
        hashtag = make_hashtag()

        hashtag_reporter = make_user()
        report_category = make_moderation_category()

        url = self._get_url(hashtag)
        headers = make_authentication_headers_for_user(hashtag_reporter)

        response = self.client.post(url, data={
            'category_id': report_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(hashtag_reporter.has_reported_hashtag_with_id(hashtag_id=hashtag.pk))
        self.assertTrue(ModerationReport.objects.filter(reporter_id=hashtag_reporter.pk,
                                                        moderated_object__object_id=hashtag.pk,
                                                        moderated_object__object_type=ModeratedObject.OBJECT_TYPE_HASHTAG,
                                                        category_id=report_category.pk
                                                        ).exists())

    def _get_url(self, hashtag):
        return reverse('report-hashtag', kwargs={
            'hashtag_name': hashtag.name
        })
