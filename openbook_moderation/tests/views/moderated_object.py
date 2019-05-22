import json

from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_auth.models import User
from openbook_common.tests.helpers import make_global_moderator, make_user, make_moderation_category, \
    make_authentication_headers_for_user, make_moderated_object_description, \
    make_community, make_fake_post_text, make_fake_post_comment_text
from openbook_communities.models import Community
from openbook_moderation.models import ModeratedObject, ModeratedObjectDescriptionChangedLog, \
    ModeratedObjectCategoryChangedLog, ModerationPenalty, ModerationCategory
from openbook_posts.models import Post, PostComment

fake = Faker()


class ModeratedObjectAPITests(APITestCase):
    """
    ModeratedObjectAPI
    """

    def test_can_update_user_moderated_object_if_global_moderator(self):
        """
        should be able to update a user moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=user.pk,
        ).exists())

    def test_can_update_user_moderated_object_if_approved(self):
        """
        should be able to update a user moderated object if approved
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=user.pk,
        ).exists())

    def test_can_update_user_moderated_object_if_rejected(self):
        """
        should be able to update a user moderated object if rejected
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)
        global_moderator.reject_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=user.pk,
        ).exists())

    def test_cant_update_moderated_object_if_verified(self):
        """
        should not be able to update a user moderated object if already verified
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object_with_id(moderated_object_id=moderated_object.pk)
        global_moderator.verify_moderated_object_with_id(moderated_object_id=moderated_object.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=report_category.pk,
            description__isnull=True,
            object_id=user.pk,
        ).exists())

    def test_cant_update_user_moderated_object_if_not_global_moderator(self):
        """
        should not be able to update a user moderated object if not a global moderator
        """
        non_global_moderator = make_user()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(non_global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=user.pk,
        ).exists())

    def test_cant_update_user_moderated_object_if_community_moderator(self):
        """
        should not be able to update a user moderated object if community moderator
        """

        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        user = make_user()
        user.join_community_with_name(community_name=community.name)

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=user.pk,
        ).exists())

    def test_creates_description_changed_log_on_update(self):
        """
        should create a description changed log on update
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(1, ModeratedObjectDescriptionChangedLog.objects.filter(
            changed_from__isnull=True,
            changed_to=new_moderated_object_description,
            log__actor_id=global_moderator.pk,
            log__moderated_object__object_id=user.pk
        ).count())

    def test_creates_category_changed_log_on_update(self):
        """
        should create a category changed log on update
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        new_moderated_object_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'category_id': new_moderated_object_category.pk,
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(1, ModeratedObjectCategoryChangedLog.objects.filter(
            changed_from=report_category,
            changed_to=new_moderated_object_category,
            log__actor_id=global_moderator.pk,
            log__moderated_object__object_id=user.pk
        ).count())

    def test_can_update_community_moderated_object_if_global_moderator(self):
        """
        should be able to update a community moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_community_with_name(community_name=community.name, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=community.pk,
        ).exists())

    def test_cant_update_community_moderated_object_if_not_global_moderator(self):
        """
        should not be able to update a community moderated object if not a global moderator
        """
        non_global_moderator = make_user()

        community = make_community()

        reporter_community = make_community()
        report_category = make_moderation_category()

        reporter_community.report_community_with_name(community_name=community.name,
                                                      category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(non_global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=community.pk,
        ).exists())

    def test_cant_update_community_moderated_object_if_community_moderator(self):
        """
        should not be able to update a community moderated object if community moderator
        """

        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            username=community_moderator.username,
            community_name=community.name)

        user = make_user()
        user.join_community_with_name(community_name=community.name)

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_community_with_name(community_name=community.name,
                                                 category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=community.pk,
        ).exists())

    def test_can_update_community_post_moderated_object_if_global_moderator(self):
        """
        should be able to update a community post moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()
        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_can_update_community_post_moderated_object_if_community_moderator(self):
        """
        should be able to update a community post moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)

        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_cant_update_community_post_moderated_object_if_not_global_nor_community_moderator(self):
        """
        should not be able to update a community post moderated object if not global nor community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        non_moderator = make_user()

        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(non_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_moderated_object_if_verified(self):
        """
        community moderator should not be able to update a community post moderated object if already verified
        """
        global_moderator = make_global_moderator()
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        global_moderator.reject_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_moderated_object_if_approved(self):
        """
        community moderator should not be able to update a community post moderated object if status is approved
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        community_moderator.approve_moderated_object_with_id(moderated_object_id=moderated_object.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_moderated_object_if_rejected(self):
        """
        community moderator should not be able to update a community post moderated object if status is rejected
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_creator = make_user()

        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        community_moderator.reject_moderated_object_with_id(moderated_object_id=moderated_object.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post.pk,
        ).exists())

    def test_can_update_community_post_comment_moderated_object_if_global_moderator(self):
        """
        should be able to update a community post_comment moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()
        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = post_comment_creator.comment_post(text=make_fake_post_comment_text(),
                                                         post=post)

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def test_can_update_community_post_comment_moderated_object_if_community_moderator(self):
        """
        should be able to update a community post_comment moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)

        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = post_comment_creator.comment_post(text=make_fake_post_comment_text(),
                                                         post=post)

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def test_cant_update_community_post_comment_moderated_object_if_not_global_nor_community_moderator(self):
        """
        should not be able to update a community post_comment moderated object if not global nor community moderator
        """
        non_global_moderator = make_user()

        community = make_community()
        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post_comment = post_comment_creator.comment_post(text=make_fake_post_comment_text(),
                                                         post=post)

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(non_global_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_comment_moderated_object_if_verified(self):
        """
        community moderator should not be able to update a community post_comment moderated object if already verified
        """
        global_moderator = make_global_moderator()
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_comment = post_comment_creator.comment_post(post=post,
                                                         text=make_fake_post_comment_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        global_moderator.reject_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_comment_moderated_object_if_approved(self):
        """
        community moderator should not be able to update a community post_comment moderated object if status is approved
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_comment = post_comment_creator.comment_post(post=post,
                                                         text=make_fake_post_comment_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        community_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def test_community_moderator_cant_update_community_post_comment_moderated_object_if_rejected(self):
        """
        community moderator should not be able to update a community post_comment moderated object if status is rejected
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()

        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username)

        post_comment_creator = make_user()

        post_comment_creator.join_community_with_name(community_name=community.name)
        post = post_comment_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post_comment = post_comment_creator.comment_post(post=post,
                                                         text=make_fake_post_comment_text())

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post=post, post_comment=post_comment, category_id=report_category.pk)

        new_moderated_object_description = make_moderated_object_description()
        new_report_category = make_moderation_category()

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        community_moderator.reject_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.patch(url, data={
            'description': new_moderated_object_description,
            'category_id': new_report_category.pk
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(ModeratedObject.objects.filter(
            category_id=new_report_category.pk,
            description=new_moderated_object_description,
            object_id=post_comment.pk,
        ).exists())

    def _get_url(self, moderated_object):
        return reverse('moderated-object', kwargs={
            'moderated_object_id': moderated_object.pk
        })


class ApproveModeratedObjectApiTests(APITestCase):
    """
    ModeratedObjectAPI
    """

    def test_can_approve_user_moderated_object_if_global_moderator(self):
        """
        should be able to approve a user moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_cant_approve_user_moderated_object_if_community_moderator(self):
        """
        should not be able to approve a user moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_cant_approve_user_moderated_object_if_regular_user(self):
        """
        should not be able to approve a user moderated object if regular user
        """
        regular_user = make_user()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_approve_community_moderated_object_if_global_moderator(self):
        """
        should be able to approve a community moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_cant_approve_community_moderated_object_if_community_moderator(self):
        """
        should not be able to approve a community moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_cant_approve_community_moderated_object_if_regular_community(self):
        """
        should not be able to approve a community moderated object if regular community
        """
        regular_community = make_user()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_community)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_approve_community_post_moderated_object_if_global_moderator(self):
        """
        should be able to approve a community_post moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_can_approve_community_post_moderated_object_if_community_post_moderator(self):
        """
        should be able to approve a community_post moderated object if community_post moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())
        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_cant_approve_community_post_moderated_object_if_regular_community_post(self):
        """
        should not be able to approve a community_post moderated object if regular community_post
        """
        regular_user = make_user()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_approve_community_post_comment_moderated_object_if_global_moderator(self):
        """
        should be able to approve a community_post_comment moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_can_approve_community_post_comment_moderated_object_if_community_post_comment_moderator(self):
        """
        should be able to approve a community_post_comment moderated object if community_post_comment moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_APPROVED
        ).exists())

    def test_cant_approve_community_post_comment_moderated_object_if_regular_community_post_comment(self):
        """
        should not be able to approve a community_post_comment moderated object if regular community_post_comment
        """
        regular_user = make_user()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def _get_url(self, moderated_object):
        return reverse('approve-moderated-object', kwargs={
            'moderated_object_id': moderated_object.pk
        })


class RejectModeratedObjectApiTests(APITestCase):
    """
    ModeratedObjectAPI
    """

    def test_can_reject_user_moderated_object_if_global_moderator(self):
        """
        should be able to reject a user moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_cant_reject_user_moderated_object_if_community_moderator(self):
        """
        should not be able to reject a user moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_cant_reject_user_moderated_object_if_regular_user(self):
        """
        should not be able to reject a user moderated object if regular user
        """
        regular_user = make_user()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_reject_community_moderated_object_if_global_moderator(self):
        """
        should be able to reject a community moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_cant_reject_community_moderated_object_if_community_moderator(self):
        """
        should not be able to reject a community moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_cant_reject_community_moderated_object_if_regular_community(self):
        """
        should not be able to reject a community moderated object if regular community
        """
        regular_community = make_user()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_community)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_reject_community_post_moderated_object_if_global_moderator(self):
        """
        should be able to reject a community_post moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_can_reject_community_post_moderated_object_if_community_post_moderator(self):
        """
        should be able to reject a community_post moderated object if community_post moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())
        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_cant_reject_community_post_moderated_object_if_regular_community_post(self):
        """
        should not be able to reject a community_post moderated object if regular community_post
        """
        regular_user = make_user()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def test_can_reject_community_post_comment_moderated_object_if_global_moderator(self):
        """
        should be able to reject a community_post_comment moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_can_reject_community_post_comment_moderated_object_if_community_post_comment_moderator(self):
        """
        should be able to reject a community_post_comment moderated object if community_post_comment moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_REJECTED
        ).exists())

    def test_cant_reject_community_post_comment_moderated_object_if_regular_community_post_comment(self):
        """
        should not be able to reject a community_post_comment moderated object if regular community_post_comment
        """
        regular_user = make_user()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            status=ModeratedObject.STATUS_PENDING
        ).exists())

    def _get_url(self, moderated_object):
        return reverse('reject-moderated-object', kwargs={
            'moderated_object_id': moderated_object.pk
        })


class VerifyModeratedObjectApiTests(APITestCase):
    """
    VerifyModeratedObjectApi
    """

    def test_verifying_approved_any_severity_post_comment_moderated_object_soft_deletes_it(self):
        """
        verifying an approved any severity post_comment moderated object should soft delete it
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()
        moderation_category_severities = self._get_moderation_category_severities()

        for moderation_category_severity in moderation_category_severities:
            post_comment_creator = make_user()
            post = post_comment_creator.create_public_post(text=make_fake_post_text())
            post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_comment_text())

            report_category = make_moderation_category(severity=moderation_category_severity)

            reporter_user.report_comment_for_post(post_comment=post_comment, post=post, category_id=report_category.pk)

            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
                post_comment=post_comment,
                category_id=report_category.pk)

            global_moderator.approve_moderated_object(moderated_object=moderated_object)

            url = self._get_url(moderated_object=moderated_object)
            headers = make_authentication_headers_for_user(global_moderator)
            response = self.client.post(url, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertTrue(PostComment.objects.filter(
                pk=post_comment.pk,
                is_deleted=True,
            ).exists())

    def test_verifying_approved_any_severity_community_moderated_object_soft_deletes_it(self):
        """
        verifying an approved any severity community moderated object should soft delete it
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()
        moderation_category_severities = self._get_moderation_category_severities()

        for moderation_category_severity in moderation_category_severities:
            community_creator = make_user()
            community = make_community(creator=community_creator)

            report_category = make_moderation_category(severity=moderation_category_severity)

            reporter_user.report_community(community=community, category_id=report_category.pk)

            moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                            category_id=report_category.pk)

            global_moderator.approve_moderated_object(moderated_object=moderated_object)

            url = self._get_url(moderated_object=moderated_object)
            headers = make_authentication_headers_for_user(global_moderator)
            response = self.client.post(url, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertTrue(Community.objects.filter(
                pk=community.pk,
                is_deleted=True,
            ).exists())

    def test_verifying_approved_any_severity_post_moderated_object_soft_deletes_it(self):
        """
        verifying an approved any severity post moderated object should soft delete it
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()
        moderation_category_severities = self._get_moderation_category_severities()

        for moderation_category_severity in moderation_category_severities:
            post_creator = make_user()
            post = post_creator.create_public_post(text=make_fake_post_text())

            report_category = make_moderation_category(severity=moderation_category_severity)

            reporter_user.report_post(post=post, category_id=report_category.pk)

            moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                       category_id=report_category.pk)

            global_moderator.approve_moderated_object(moderated_object=moderated_object)

            url = self._get_url(moderated_object=moderated_object)
            headers = make_authentication_headers_for_user(global_moderator)
            response = self.client.post(url, **headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertTrue(Post.objects.filter(
                pk=post.pk,
                is_deleted=True,
            ).exists())

    def test_verifying_approved_critical_severity_user_moderated_object_soft_deletes_it(self):
        """
        verifying an approved critical severity user moderated object should soft delete it
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        user = make_user()

        report_category = make_moderation_category(severity=ModerationCategory.SEVERITY_CRITICAL)

        reporter_user.report_user(user=user, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(User.objects.filter(
            pk=user.pk,
            is_deleted=True,
        ).exists())

    def test_verifying_approved_not_critical_severity_user_moderated_object_does_not_soft_delete_it(self):
        """
        verifying an approved non critical severity user moderated object should not soft delete it
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        user = make_user()

        report_category = make_moderation_category(severity=ModerationCategory.SEVERITY_HIGH)

        reporter_user.report_user(user=user, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(User.objects.filter(
            pk=user.pk,
            is_deleted=False,
        ).exists())

    def test_verifying_rejected_user_moderated_object_does_not_place_suspension_penalty_on_user(self):
        """
        verifying a rejected user moderated object should not place a suspension penalty on the user
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        user = make_user()

        report_category = make_moderation_category()

        reporter_user.report_user(user=user, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.reject_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(ModerationPenalty.objects.filter(
            moderated_object_id=moderated_object.pk,
            user_id=user.pk,
            expiration__isnull=False
        ).exists())

    def test_verifying_approved_user_moderated_object_places_suspension_penalty_on_user(self):
        """
        verifying an approved user moderated object should place a suspension penalty on the user
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        user = make_user()

        report_category = make_moderation_category()

        reporter_user.report_user(user=user, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModerationPenalty.objects.filter(
            moderated_object_id=moderated_object.pk,
            user_id=user.pk,
            expiration__isnull=False
        ).exists())

    def test_verifying_approved_post_moderated_object_places_suspension_penalty_on_creator(self):
        """
        verifying an approved post moderated object should place a suspension penalty on the creator
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        report_category = make_moderation_category()

        reporter_user.report_post(post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(post=post,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModerationPenalty.objects.filter(
            moderated_object_id=moderated_object.pk,
            user_id=post_creator.pk,
            expiration__isnull=False
        ).exists())

    def test_verifying_approved_community_moderated_object_places_suspension_penalty_on_staff(self):
        """
        verifying an approved community moderated object should place a suspension penalty on the staff
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=community_moderator.username,
                                                                             community_name=community.name)

        community_administrator = make_user()
        community_administrator.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(
            username=community_administrator.username,
            community_name=community.name)

        report_category = make_moderation_category()

        reporter_user.report_community(community=community, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(3, ModerationPenalty.objects.filter(
            moderated_object_id=moderated_object.pk,
            user_id__in=[community_creator.pk, community_moderator.pk, community_administrator.pk],
            expiration__isnull=False
        ).count())

    def test_verifying_approved_post_comment_moderated_object_places_suspension_penalty_on_creator(self):
        """
        verifying an approved post comment moderated object should place a suspension penalty on the creator
        """
        global_moderator = make_global_moderator()

        reporter_user = make_user()

        post_comment_creator = make_user()
        post = post_comment_creator.create_public_post(text=make_fake_post_text())
        post_comment = post_comment_creator.comment_post(post=post, text=make_fake_post_comment_text())

        report_category = make_moderation_category()

        reporter_user.report_comment_for_post(post_comment=post_comment, post=post, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(post_comment=post_comment,
                                                                                           category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModerationPenalty.objects.filter(
            moderated_object_id=moderated_object.pk,
            user_id=post_comment_creator.pk,
            expiration__isnull=False
        ).exists())

    def test_can_verify_moderated_object_if_global_moderator_and_approved(self):
        """
        should be able to verify a user moderated object if global moderator and approved
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=True
        ).exists())

    def test_can_verify_moderated_object_if_global_moderator_and_rejected(self):
        """
        should be able to verify a user moderated object if global moderator and rejected
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.reject_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=True
        ).exists())

    def test_cant_verify_moderated_object_if_global_moderator_and_pending(self):
        """
        should not be able to verify a user moderated object if global moderator and pending
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            status=ModeratedObject.STATUS_PENDING,
            verified=False
        ).exists())

    def test_cant_verify_user_moderated_object_if_community_moderator(self):
        """
        should not be able to verify a user moderated object if community moderator
        """

        global_moderator = make_global_moderator()

        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=False
        ).exists())

    def test_cant_verify_user_moderated_object_if_regular_user(self):
        """
        should not be able to verify a user moderated object if regular user
        """
        regular_user = make_user()
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=False
        ).exists())

    def test_can_verify_community_moderated_object_if_global_moderator(self):
        """
        should be able to verify a community moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=True
        ).exists())

    def test_cant_verify_community_moderated_object_if_community_moderator(self):
        """
        should not be able to verify a community moderated object if community moderator
        """

        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)
        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=False
        ).exists())

    def test_cant_verify_community_moderated_object_if_regular_user(self):
        """
        should not be able to verify a community moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=False
        ).exists())

    def test_can_verify_community_post_moderated_object_if_global_moderator(self):
        """
        should be able to verify a community_post moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=True
        ).exists())

    def test_cant_verify_community_post_moderated_object_if_community_moderator(self):
        """
        should not be able to verify a community_post moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())
        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)
        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=False
        ).exists())

    def test_cant_verify_community_post_moderated_object_if_regular_user(self):
        """
        should not be able to verify a community_post moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=False
        ).exists())

    def test_can_verify_community_post_comment_moderated_object_if_global_moderator(self):
        """
        should be able to verify a community_post_comment moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=True
        ).exists())

    def test_cant_verify_community_post_comment_moderated_object_if_community_moderator(self):
        """
        should not be able to verify a community_post_comment moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=False
        ).exists())

    def test_cant_verify_community_post_comment_moderated_object_if_regular_user(self):
        """
        should not be able to verify a community_post_comment moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=False
        ).exists())

    def _get_url(self, moderated_object):
        return reverse('verify-moderated-object', kwargs={
            'moderated_object_id': moderated_object.pk
        })

    def _get_moderation_category_severities(self):
        return (
            ModerationCategory.SEVERITY_CRITICAL,
            ModerationCategory.SEVERITY_HIGH,
            ModerationCategory.SEVERITY_MEDIUM,
            ModerationCategory.SEVERITY_LOW,
        )


class UnverifyModeratedObjectApiTests(APITestCase):
    """
    UnverifyModeratedObjectApi
    """

    def test_can_unverify_moderated_object_if_global_moderator_and_approved(self):
        """
        should be able to unverify a user moderated object if global moderator and approved
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=False
        ).exists())

    def test_can_unverify_moderated_object_if_global_moderator_and_rejected(self):
        """
        should be able to unverify a user moderated object if global moderator and rejected
        """
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.reject_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=False
        ).exists())

    def test_cant_unverify_user_moderated_object_if_community_moderator(self):
        """
        should not be able to unverify a user moderated object if community moderator
        """

        global_moderator = make_global_moderator()

        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=True
        ).exists())

    def test_cant_unverify_user_moderated_object_if_regular_user(self):
        """
        should not be able to unverify a user moderated object if regular user
        """
        regular_user = make_user()
        global_moderator = make_global_moderator()

        user = make_user()

        reporter_user = make_user()
        report_category = make_moderation_category()

        reporter_user.report_user_with_username(username=user.username, category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_user(user=user,
                                                                                   category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=user.pk,
            verified=True
        ).exists())

    def test_can_unverify_community_moderated_object_if_global_moderator(self):
        """
        should be able to unverify a community moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=False
        ).exists())

    def test_cant_unverify_community_moderated_object_if_community_moderator(self):
        """
        should not be able to unverify a community moderated object if community moderator
        """

        community_creator = make_user()
        community = make_community(creator=community_creator)
        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(community_name=community.name,
                                                                             username=community_moderator.username
                                                                             )

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)
        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=True
        ).exists())

    def test_cant_unverify_community_moderated_object_if_regular_user(self):
        """
        should not be able to unverify a community moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        reporter_community = make_user()
        report_category = make_moderation_category()

        reporter_community.report_community(community=community,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_community(community=community,
                                                                                        category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community.pk,
            verified=True
        ).exists())

    def test_can_unverify_community_post_moderated_object_if_global_moderator(self):
        """
        should be able to unverify a community_post moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=False
        ).exists())

    def test_cant_unverify_community_post_moderated_object_if_community_moderator(self):
        """
        should not be able to unverify a community_post moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())
        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)
        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=True
        ).exists())

    def test_cant_unverify_community_post_moderated_object_if_regular_user(self):
        """
        should not be able to unverify a community_post moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_creator.create_community_post(community_name=community.name,
                                                                      text=make_fake_post_text())

        reporter_community_post = make_user()
        report_category = make_moderation_category()

        reporter_community_post.report_post(post=community_post,
                                            category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post(
            post=community_post,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post.pk,
            verified=True
        ).exists())

    def test_can_unverify_community_post_comment_moderated_object_if_global_moderator(self):
        """
        should be able to unverify a community_post_comment moderated object if global moderator
        """
        global_moderator = make_global_moderator()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(global_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=False
        ).exists())

    def test_cant_unverify_community_post_comment_moderated_object_if_community_moderator(self):
        """
        should not be able to unverify a community_post_comment moderated object if community moderator
        """
        community_creator = make_user()
        community = make_community(creator=community_creator)

        community_moderator = make_user()
        community_moderator.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(
            community_name=community.name,
            username=community_moderator.username
        )

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(community_moderator)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=True
        ).exists())

    def test_cant_unverify_community_post_comment_moderated_object_if_regular_user(self):
        """
        should not be able to unverify a community_post_comment moderated object if regular user
        """
        regular_user = make_user()

        community = make_community()

        community_post_comment_creator = make_user()
        community_post_comment_creator.join_community_with_name(community_name=community.name)
        community_post = community_post_comment_creator.create_community_post(
            community_name=community.name,
            text=make_fake_post_text())
        community_post_comment = community_post_comment_creator.comment_post(
            post=community_post,
            text=make_fake_post_text())

        reporter_community_post_comment = make_user()
        report_category = make_moderation_category()

        reporter_community_post_comment.report_comment_for_post(post=community_post,
                                                                post_comment=community_post_comment,
                                                                category_id=report_category.pk)

        moderated_object = ModeratedObject.get_or_create_moderated_object_for_post_comment(
            post_comment=community_post_comment,
            category_id=report_category.pk)

        global_moderator = make_global_moderator()
        global_moderator.approve_moderated_object(moderated_object=moderated_object)
        global_moderator.verify_moderated_object(moderated_object=moderated_object)

        url = self._get_url(moderated_object=moderated_object)
        headers = make_authentication_headers_for_user(regular_user)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(ModeratedObject.objects.filter(
            object_id=community_post_comment.pk,
            verified=True
        ).exists())

    def _get_url(self, moderated_object):
        return reverse('unverify-moderated-object', kwargs={
            'moderated_object_id': moderated_object.pk
        })
