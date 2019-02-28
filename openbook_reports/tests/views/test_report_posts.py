import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from mixer.backend.django import mixer
from rest_framework.test import APITestCase
import logging
from openbook_auth.models import User
from openbook_common.tests.helpers import make_fake_post_text, make_user, make_authentication_headers_for_user, \
    make_circle, make_community, make_superuser, make_report_category, make_report_comment_text, \
    make_member_of_community_with_admin

logger = logging.getLogger(__name__)
fake = Faker()


class PostReportAPITests(APITestCase):
    """
    PostReportAPI Tests
    """
    fixtures = [
        'openbook_reports/fixtures/report_categories.json'
    ]

    def test_can_create_post_report(self):
        """
        should be able to report a post with valid data
        """
        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())

        reporting_user = make_user()
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = self._get_post_report_data()

        response = self.client.put(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_post_report_twice(self):
        """
        should not be able to report same post again
        """
        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())

        reporting_user = make_user()
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = self._get_post_report_data()

        response_first = self.client.put(url, data, **headers)
        response_second = self.client.put(url, data, **headers)

        self.assertEqual(response_second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_post_report_with_invalid_report_category(self):
        """
        should not be able to report a post with invalid report category name
        """
        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())

        reporting_user = make_user()
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = {
            'category_name': 'invalid_category',
            'comment': 'This is spam'
        }

        response = self.client.put(url, data, **headers)
        parsed_response = json.loads(response.content)

        self.assertIn('category_name', parsed_response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_post_report_for_private_posts(self):
        """
        should not be able to report a post to which the user has no access
        """
        user = make_user()
        circle = make_circle(user)
        post = user.create_encircled_post(text= make_fake_post_text(), circles_ids=[circle.pk])

        reporting_user = make_user()
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = self._get_post_report_data()

        response = self.client.put(url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_post_report_for_community_post(self):
        """
        should be able to report a communtiy post with valid data
        """
        user = make_user()
        community = make_community(user, type='T')
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        reporting_user = make_user()
        user.invite_user_with_username_to_community_with_name(username=reporting_user.username, community_name=community.name)
        reporting_user.join_community_with_name(community.name)
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = self._get_post_report_data()

        response = self.client.put(url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_post_report_for_community_user_not_part_of(self):
        """
        should not be able to report a community post of a community user is not part of
        """
        user = make_user()
        community = make_community(user, type='T')
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        reporting_user = make_user()
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_post_report_url(post)
        data = self._get_post_report_data()

        response = self.client.put(url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_confirm_public_post_report(self):
        """
        should be able to confirm a public post report if superuser
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_superuser()
        headers = make_authentication_headers_for_user(confirming_user)
        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_confirm_public_post_report_if_not_superuser(self):
        """
        should not be able to confirm a public post report if the user is not a superuser
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_user()
        headers = make_authentication_headers_for_user(confirming_user)
        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_reject_public_post_report(self):
        """
        should be able to reject a public post report if superuser
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_superuser()
        headers = make_authentication_headers_for_user(confirming_user)
        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_reject_public_post_report_if_not_superuser(self):
        """
        should not be able to reject a public post report if the user is not a superuser
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_user()
        headers = make_authentication_headers_for_user(confirming_user)
        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_reject_public_post_report_that_is_already_confirmed(self):
        """
        should not be able to reject a public post report if its already been confirmed
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_superuser()
        headers = make_authentication_headers_for_user(confirming_user)
        confirming_user.confirm_report_with_id_for_post_with_id(report_id=post_report.pk, post_id=post.pk)

        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_confirm_public_post_report_that_is_already_rejected(self):
        """
        should not be able to confirm a public post report if its already been rejected
        """

        user, reporting_user, post, post_report = self._make_post_report_for_public_post()

        confirming_user = make_superuser()
        headers = make_authentication_headers_for_user(confirming_user)
        confirming_user.reject_report_with_id_for_post_with_id(report_id=post_report.pk, post_id=post.pk)

        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_confirm_post_report_for_community(self):
        """
        should be able to confirm a community post report if admin
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        headers = make_authentication_headers_for_user(admin)
        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_reject_post_report_for_community(self):
        """
        should be able to reject a community post report if admin
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        headers = make_authentication_headers_for_user(admin)
        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_confirm_post_report_for_community_if_superuser(self):
        """
        should be able to confirm a community post report if superuser
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        user = make_superuser()
        headers = make_authentication_headers_for_user(user)
        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_reject_post_report_for_community_as_superuser(self):
        """
        should be able to reject a community post report if superuser
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        user = make_superuser()
        headers = make_authentication_headers_for_user(user)
        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_confirm_post_report_for_community_if_regular_user(self):
        """
        should not be able to reject a community post report if not admin or superuser
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        user = make_user()
        headers = make_authentication_headers_for_user(user)
        url = self._get_post_report_confirm_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_reject_post_report_for_community_if_regular_user(self):
        """
        should not be able to reject a community post report if not admin or superuser
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()

        user = make_user()
        headers = make_authentication_headers_for_user(user)
        url = self._get_post_report_reject_url(post, post_report)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_see_their_own_post_reports(self):
        """
        should be able to see self-reported posts
        """
        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())
        post_two = user.create_public_post(text=make_fake_post_text())

        reporting_user = make_user()
        post_report = reporting_user.report_post_with_id(post_id=post.pk, category_name=make_report_category().name)
        post_report_two = reporting_user.report_post_with_id(post_id=post_two.pk, category_name=make_report_category().name)
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_all_reports_url()

        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_see_their_own_post_reports_for_post(self):
        """
        should be able to see all self reported post reports for post with id
        """
        user, reporting_user, post, post_report = self._make_post_report_for_public_post()
        random_user = make_user()
        # report post from a diff user
        random_user.report_post_with_id(post_id=post.pk, category_name=make_report_category().name)
        headers = make_authentication_headers_for_user(reporting_user)

        url = self._get_reports_for_post_url(post)
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 1)
        self.assertEqual(parsed_response[0]['id'], post_report.pk)
        self.assertEqual(parsed_response[0]['comment'], post_report.comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_can_see_all_post_reports_for_post(self):
        """
        should be able to see all reported post reports for post with id if superuser
        """
        user, reporting_user, post, post_report = self._make_post_report_for_public_post()
        random_user = make_user()
        # report post from a diff user
        random_user.report_post_with_id(post_id=post.pk, category_name=make_report_category().name)

        superuser = make_superuser()
        headers = make_authentication_headers_for_user(superuser)

        url = self._get_reports_for_post_url(post)
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_moderator_can_see_all_post_reports_for_post_in_community(self):
        """
        should be able to see all reported post reports for post with id if community moderator
        """
        admin = make_user()
        community = make_community(admin, type='T')
        post = admin.create_community_post(text=make_fake_post_text(), community_name=community.name)

        # report post once
        reporting_user = make_user()
        admin.invite_user_with_username_to_community_with_name(username=reporting_user.username, community_name=community.name)
        reporting_user.join_community_with_name(community.name)
        post_report = reporting_user.report_post_with_id(post_id=post.pk,
                                                         category_name=make_report_category().name,
                                                         comment=make_report_comment_text())

        # report post second time diff user
        reporting_user_two = make_user()
        admin.invite_user_with_username_to_community_with_name(username=reporting_user_two.username,
                                                               community_name=community.name)
        reporting_user_two.join_community_with_name(community.name)
        post_report_two = reporting_user_two.report_post_with_id(post_id=post.pk,
                                                                 category_name=make_report_category().name,
                                                                 comment=make_report_comment_text())

        headers = make_authentication_headers_for_user(admin)

        url = self._get_reports_for_post_url(post)
        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 2)
        report_one = parsed_response[0]
        report_two = parsed_response[1]
        self.assertTrue(report_one['comment'] == post_report.comment)
        self.assertTrue(report_two['comment'] == post_report_two.comment)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_see_all_post_reports_from_community_if_moderator(self):
        """
        should be able to see all reported posts if community moderator
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()
        reporting_user_two = make_member_of_community_with_admin(community, admin)
        post_report_two = reporting_user_two.report_post_with_id(post_id=post.pk,
                                                                 comment=make_report_comment_text(),
                                                                 category_name=make_report_category().name)

        headers = make_authentication_headers_for_user(admin)
        url = self._get_all_community_reports_url(community)

        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 1)  # should return the one post
        post_reports = parsed_response[0]['reports']
        self.assertTrue(len(post_reports) == 2)  # should return both reports for that post
        self.assertEqual(post_reports[0]['id'], post_report.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_see_all_post_reports_from_community_if_not_moderator(self):
        """
        should not be able to see all reported posts if not community moderator
        """

        community, reporting_user, admin, post, post_report = self._make_post_report_for_community_post()
        # create another post and report it
        post_two = reporting_user.create_community_post(text=make_fake_post_text(),
                                                        community_name=community.name)

        reporting_user_two = make_member_of_community_with_admin(community, admin)
        post_report_two = reporting_user_two.report_post_with_id(post_id=post_two.pk,
                                                                 category_name=make_report_category().name)

        headers = make_authentication_headers_for_user(reporting_user)
        url = self._get_all_community_reports_url(community)

        response = self.client.get(url, **headers)
        parsed_response = json.loads(response.content)

        self.assertTrue(len(parsed_response) == 1)
        post_reports = parsed_response[0]['reports']
        self.assertEqual(parsed_response[0]['id'], post.id)
        self.assertEqual(post_reports[0]['id'], post_report.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _make_post_report_for_public_post(self):
        user = make_user()
        post = user.create_public_post(text=make_fake_post_text())

        reporting_user = make_user()
        post_report = reporting_user.report_post_with_id(post_id=post.pk,
                                                         category_name=make_report_category().name,
                                                         comment=make_report_comment_text())

        return user, reporting_user, post, post_report

    def _make_post_report_for_community_post(self):
        admin = make_user()
        community = make_community(admin, type='T')
        post = admin.create_community_post(text=make_fake_post_text(), community_name=community.name)

        reporting_user = make_user()
        admin.invite_user_with_username_to_community_with_name(username=reporting_user.username, community_name=community.name)
        reporting_user.join_community_with_name(community.name)
        post_report = reporting_user.report_post_with_id(post_id=post.pk, category_name=make_report_category().name)

        return community, reporting_user, admin, post, post_report

    def _get_all_reports_url(self):
        return reverse('reported-posts')

    def _get_all_community_reports_url(self, community):
        return reverse('community-reported-posts', kwargs={
            'community_name': community.name
        })

    def _get_reports_for_post_url(self, post):
        return reverse('report-post', kwargs={
            'post_id': post.pk
        })

    def _get_post_report_data(self):
        return {
            'category_name': 'spam',
            'comment': 'This is spam'
        }

    def _get_post_report_confirm_url(self, post, post_report):
        return reverse('post-report-confirm', kwargs={
            'post_id': post.pk,
            'report_id': post_report.pk
        })

    def _get_post_report_reject_url(self, post, post_report):
        return reverse('post-report-confirm', kwargs={
            'post_id': post.pk,
            'report_id': post_report.pk
        })

    def _get_post_report_url(self, post):
        return reverse('report-post', kwargs={
            'post_id': post.pk
        })
